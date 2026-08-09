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

for variable in ODOO_BIN ODOO_DB ODOO_ADDONS_DIR ODOO_SERVICE ODOO_USER ODOO_GROUP FINANCA_DOMAIN; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $env_file"
done

[[ -x "$ODOO_BIN" ]] || die "ODOO_BIN is not executable: $ODOO_BIN"
[[ -d "$ODOO_ADDONS_DIR" ]] || die "ODOO_ADDONS_DIR does not exist: $ODOO_ADDONS_DIR"
[[ -d "$staged_addon" ]] || die "staged addon directory does not exist: $staged_addon"
[[ -f "$staged_addon/__manifest__.py" ]] || die "staged directory is not an Odoo addon"
[[ -d "$deployment_scripts" ]] || die "deployment scripts directory does not exist"
[[ "$ODOO_ADDONS_DIR" != "/" ]] || die "ODOO_ADDONS_DIR cannot be /"

command -v rsync >/dev/null || die "rsync is required on the server"
command -v runuser >/dev/null || die "runuser is required on the server"
command -v systemctl >/dev/null || die "systemctl is required on the server"

require_ga4=${REQUIRE_GA4:-true}
target_addon="${ODOO_ADDONS_DIR%/}/financa_website"
release_dir=$(mktemp -d "${ODOO_ADDONS_DIR%/}/.financa_website.next.XXXXXX")
backup_addon="${ODOO_ADDONS_DIR%/}/.financa_website.previous.$(date +%Y%m%d%H%M%S)"
failed_addon="${ODOO_ADDONS_DIR%/}/.financa_website.failed.$(date +%Y%m%d%H%M%S)"
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

run_odoo_upgrade() {
    runuser -u "$ODOO_USER" -- \
        "$ODOO_BIN" "${odoo_config_args[@]}" -d "$ODOO_DB" \
        -u financa_website --stop-after-init
}

rollback() {
    status=$?
    if [[ $status -eq 0 ]]; then
        return
    fi

    printf 'Deployment failed; restoring the previous addon directory when possible.\n' >&2
    if [[ $swapped == true && -e "$backup_addon" ]]; then
        mv "$target_addon" "$failed_addon" || true
        mv "$backup_addon" "$target_addon" || true
    fi
    if [[ $service_stopped == true ]]; then
        systemctl start "$ODOO_SERVICE" || true
    fi
    exit "$status"
}
trap rollback ERR

run_odoo_shell "$deployment_scripts/preflight_financa.py"

rsync -a --exclude='__pycache__' --exclude='*.pyc' "$staged_addon/" "$release_dir/"
chown -R "$ODOO_USER:$ODOO_GROUP" "$release_dir"

systemctl stop "$ODOO_SERVICE"
service_stopped=true

if [[ -e "$target_addon" ]]; then
    mv "$target_addon" "$backup_addon"
fi
mv "$release_dir" "$target_addon"
swapped=true

run_odoo_upgrade
run_odoo_shell "$deployment_scripts/configure_financa.py"
run_odoo_shell "$deployment_scripts/postflight_financa.py"

systemctl start "$ODOO_SERVICE"
service_stopped=false
trap - ERR

printf 'Deployment completed. Previous addon backup: %s\n' "$backup_addon"

