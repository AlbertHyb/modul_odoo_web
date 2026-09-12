#!/usr/bin/env bash
# Deploy one staged financa_website addon into an Odoo server.
set -Eeuo pipefail

die() {
    printf 'DEPLOY FAILED: %s\n' "$*" >&2
    exit 1
}

[[ ${EUID} -eq 0 ]] || die "run this script as root (usually through sudo -n)"

staged_addon=${1:?usage: deploy_financa.sh <staged-addon-dir> <deployment-scripts-dir>}
deployment_scripts=${2:?usage: deploy_financa.sh <staged-addon-dir> <deployment-scripts-dir>}
env_file=${FINANCA_DEPLOY_ENV:-/etc/financa/deploy.env}

[[ -f "$env_file" ]] || die "missing server configuration: $env_file"
# shellcheck disable=SC1090
source "$env_file"

for variable in ODOO_BIN ODOO_DB ODOO_ADDONS_DIR ODOO_SERVICE ODOO_USER ODOO_GROUP FINANCA_DOMAIN FINANCA_BACKUP_BIN FINANCA_RESTORE_BIN; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $env_file"
done

[[ -x "$ODOO_BIN" ]] || die "ODOO_BIN is not executable: $ODOO_BIN"
[[ -d "$ODOO_ADDONS_DIR" ]] || die "ODOO_ADDONS_DIR does not exist: $ODOO_ADDONS_DIR"
[[ -d "$staged_addon" ]] || die "staged addon directory does not exist: $staged_addon"
[[ -f "$staged_addon/__manifest__.py" ]] || die "staged directory is not an Odoo addon"
[[ -d "$deployment_scripts" ]] || die "deployment scripts directory does not exist"
[[ -f "$deployment_scripts/module_state_financa.py" ]] || die "module state script is missing"
[[ "$ODOO_ADDONS_DIR" != "/" ]] || die "ODOO_ADDONS_DIR cannot be /"

for command in flock realpath rsync runuser stat systemctl; do
    command -v "$command" >/dev/null || die "$command is required on the server"
done

validate_root_executable() {
    local path=$1 mode
    [[ "$path" == /* && -f "$path" && -x "$path" && ! -L "$path" ]] \
        || die "recovery hook must be a regular executable: $path"
    [[ "$(realpath -- "$path")" == "$path" ]] || die "recovery hook path must be canonical: $path"
    [[ $(stat -c '%u' "$path") -eq 0 ]] || die "recovery hook must be owned by root: $path"
    mode=$(stat -c '%a' "$path")
    (( (8#$mode & 8#22) == 0 )) || die "recovery hook cannot be group/world writable: $path"
}

validate_root_executable "$FINANCA_BACKUP_BIN"
validate_root_executable "$FINANCA_RESTORE_BIN"

exec 9>/run/lock/financa_website.lock
flock -n 9 || die "another Financa deployment is already running"

require_ga4=${REQUIRE_GA4:-true}
target_addon="${ODOO_ADDONS_DIR%/}/financa_website"
release_dir=$(mktemp -d "${ODOO_ADDONS_DIR%/}/.financa_website.next.XXXXXX")
backup_addon="${ODOO_ADDONS_DIR%/}/.financa_website.previous.$(date +%Y%m%d%H%M%S)"
failed_addon="${ODOO_ADDONS_DIR%/}/.financa_website.failed.$(date +%Y%m%d%H%M%S)"
module_action=
recovery_point=
backup_created=false
backup_addon_moved=false
swapped=false
service_stopped=false

odoo_config_args=()
if [[ -n ${ODOO_CONFIG:-} ]]; then
    [[ -f "$ODOO_CONFIG" ]] || die "ODOO_CONFIG does not exist: $ODOO_CONFIG"
    odoo_config_args=(-c "$ODOO_CONFIG")
fi

run_odoo_shell() {
    local script=$1
    runuser -u "$ODOO_USER" -- env \
        FINANCA_DOMAIN="$FINANCA_DOMAIN" \
        REQUIRE_GA4="$require_ga4" \
        "$ODOO_BIN" "${odoo_config_args[@]}" shell -d "$ODOO_DB" < "$script"
}

detect_module_action() {
    local output
    output=$(run_odoo_shell "$deployment_scripts/module_state_financa.py")
    module_action=$(sed -n 's/^FINANCA_MODULE_ACTION=//p' <<< "$output")
    [[ "$module_action" == "install" || "$module_action" == "update" ]] \
        || die "could not determine whether to install or update financa_website"
}

run_odoo_module_action() {
    if [[ $module_action == "install" ]]; then
        runuser -u "$ODOO_USER" -- \
            "$ODOO_BIN" "${odoo_config_args[@]}" -d "$ODOO_DB" \
            -i financa_website --stop-after-init
    else
        runuser -u "$ODOO_USER" -- \
            "$ODOO_BIN" "${odoo_config_args[@]}" -d "$ODOO_DB" \
            -u financa_website --stop-after-init
    fi
}

create_recovery_point() {
    recovery_point=$("$FINANCA_BACKUP_BIN" "$ODOO_DB")
    if [[ -z "$recovery_point" || "$recovery_point" == *$'\n'* \
        || ! "$recovery_point" =~ ^[A-Za-z0-9._:/-]+$ ]]; then
        printf 'DEPLOY FAILED: backup hook did not return one valid recovery token\n' >&2
        return 1
    fi
    backup_created=true
    printf 'Recovery point created: %s\n' "$recovery_point"
}

rollback() {
    local status=$? recovered=true
    trap - ERR
    [[ $status -ne 0 ]] || return

    printf 'Deployment failed; restoring code and data when possible.\n' >&2
    if [[ $swapped == true && -e "$target_addon" ]]; then
        mv "$target_addon" "$failed_addon" || recovered=false
    fi
    if [[ $backup_addon_moved == true && -e "$backup_addon" ]]; then
        if [[ -e "$target_addon" ]]; then
            recovered=false
        else
            mv "$backup_addon" "$target_addon" || recovered=false
        fi
    fi
    if [[ $backup_created == true ]]; then
        "$FINANCA_RESTORE_BIN" "$ODOO_DB" "$recovery_point" || recovered=false
    fi

    if [[ $service_stopped == true ]]; then
        if [[ $recovered == true ]]; then
            systemctl start "$ODOO_SERVICE" || recovered=false
        fi
        if [[ $recovered != true ]]; then
            printf 'RECOVERY FAILED: service remains stopped; manual intervention is required.\n' >&2
        fi
    fi
    exit "$status"
}
trap rollback ERR

detect_module_action
run_odoo_shell "$deployment_scripts/preflight_financa.py"

rsync -a --exclude='__pycache__' --exclude='*.pyc' "$staged_addon/" "$release_dir/"
chown -R "$ODOO_USER:$ODOO_GROUP" "$release_dir"

systemctl stop "$ODOO_SERVICE"
service_stopped=true
create_recovery_point

if [[ -e "$target_addon" ]]; then
    mv "$target_addon" "$backup_addon"
    backup_addon_moved=true
fi
mv "$release_dir" "$target_addon"
swapped=true

run_odoo_module_action
run_odoo_shell "$deployment_scripts/ensure_financa_homepage.py"
run_odoo_shell "$deployment_scripts/configure_financa.py"
run_odoo_shell "$deployment_scripts/postflight_financa.py"

systemctl start "$ODOO_SERVICE"
service_stopped=false
trap - ERR

printf 'Deployment completed with action %s. Recovery point: %s\n' "$module_action" "$recovery_point"
