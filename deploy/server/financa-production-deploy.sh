#!/usr/bin/env bash
set -Eeuo pipefail

readonly repo=/srv/financa-production/repo
readonly releases=/srv/financa-production/releases
readonly current="$releases/current"
readonly render_root=/srv/financa-production/render
readonly env_file=/etc/financa-production/deploy.env

die() {
    printf 'PRODUCTION DEPLOY FAILED: %s\n' "$*" >&2
    exit 1
}

[[ ${EUID} -eq 0 ]] || die 'must run as root'
[[ ${SSH_ORIGINAL_COMMAND:-} =~ ^deploy\ ([0-9a-f]{40})$ ]] \
    || die 'only deploy <40-char-master-sha> is allowed'
sha=${BASH_REMATCH[1]}
[[ -f "$env_file" && ! -L "$env_file" ]] || die "missing or invalid $env_file"
[[ $(stat -c '%u' "$env_file") -eq 0 ]] || die "$env_file must be owned by root"
env_mode=$(stat -c '%a' "$env_file")
(( (8#$env_mode & 8#22) == 0 )) || die "$env_file cannot be group/world writable"
# shellcheck disable=SC1090
source "$env_file"

for variable in REPO_USER PRODUCTION_DOMAIN ODOO_DB ODOO_PORT COMPOSE_ENV_FILE COMPOSE_FILE FINANCA_VERIFY_BIN FINANCA_BACKUP_BIN FINANCA_RESTORE_BIN; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $env_file"
done
[[ -d "$repo/.git" && -f "$COMPOSE_FILE" ]] || die 'production checkout is incomplete'
[[ -f "$COMPOSE_ENV_FILE" ]] || die "missing Compose environment: $COMPOSE_ENV_FILE"
[[ "$PRODUCTION_DOMAIN" =~ ^https://[A-Za-z0-9.-]+$ ]] || die 'PRODUCTION_DOMAIN must be one HTTPS hostname'

for command in cmp curl docker flock mktemp realpath rm runuser stat tar; do
    command -v "$command" >/dev/null || die "$command is required"
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
validate_root_executable "$FINANCA_VERIFY_BIN"

validate_root_file() {
    local path=$1 mode
    [[ "$path" == /* && -f "$path" && ! -L "$path" ]] || die "trusted file is invalid: $path"
    [[ "$(realpath -- "$path")" == "$path" ]] || die "trusted file path must be canonical: $path"
    [[ $(stat -c '%u' "$path") -eq 0 ]] || die "trusted file must be owned by root: $path"
    mode=$(stat -c '%a' "$path")
    (( (8#$mode & 8#22) == 0 )) || die "trusted file cannot be group/world writable: $path"
}

validate_root_file "$COMPOSE_FILE"
validate_root_file "$COMPOSE_ENV_FILE"
source_export=
staged_release=
cleanup_render() {
    [[ -z ${source_export:-} || ! -e "$source_export" ]] || rm -rf -- "$source_export"
    [[ -z ${staged_release:-} || ! -e "$staged_release" ]] || rm -rf -- "$staged_release"
}
trap cleanup_render EXIT


exec 9>/run/lock/financa-production-deploy.lock
flock -n 9 || die 'another production deployment is running'

compose=(docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE")
[[ "$("${compose[@]}" config --services | sort)" == $'db\nodoo' ]] \
    || die 'Compose must contain exactly db and odoo services'
while IFS= read -r image; do
    [[ "$image" == *@sha256:* ]] || die "Compose image is not pinned by digest: $image"
done < <("${compose[@]}" config --images)
"${compose[@]}" run --rm --no-deps odoo odoo --version | grep -Fq '19.0' \
    || die 'the production Odoo image is not version 19.0'

runuser -u "$REPO_USER" -- git -C "$repo" fetch --quiet origin master
[[ $(runuser -u "$REPO_USER" -- git -C "$repo" rev-parse origin/master) == "$sha" ]] \
    || die 'requested SHA is not the current origin/master tip'
[[ -z $(runuser -u "$REPO_USER" -- git -C "$repo" status --porcelain --untracked-files=all) ]] \
    || die 'production checkout is not clean'
runuser -u "$REPO_USER" -- git -C "$repo" checkout --detach --quiet "$sha"
[[ -z $(runuser -u "$REPO_USER" -- git -C "$repo" status --porcelain --untracked-files=all) ]] \
    || die 'production checkout changed while selecting the approved SHA'

# This script is installed as the restricted SSH forced command, so the host keeps
# a frozen copy of it. Deploying with privileged logic that is not the reviewed
# revision would run stale steps against production, so require an exact match.
installed_command=$(realpath "${BASH_SOURCE[0]}")
expected_command="$repo/deploy/server/financa-production-deploy.sh"
cmp -s "$installed_command" "$expected_command" \
    || die "the installed forced command differs from $expected_command; reinstall it with: sudo install -o root -g root -m 0750 $expected_command $installed_command"

mkdir -p "$releases"
previous=$(readlink -f "$current")
[[ -d "$previous" ]] || die 'current release is invalid; create the documented bootstrap release first'
release="$releases/$sha"
if [[ ! -e "$release" ]]; then
    staged_release="$render_root/$sha"
    [[ ! -e "$staged_release" ]] || die "stale render directory exists: $staged_release"
    source_export=$(runuser -u "$REPO_USER" -- mktemp -d "$render_root/.source.$sha.XXXXXX")
    runuser -u "$REPO_USER" -- git -C "$repo" archive "$sha" \
        | runuser -u "$REPO_USER" -- tar -x -C "$source_export"
    runuser -u "$REPO_USER" -- python3 "$source_export/deploy/ci/render_financa_artifact.py" \
        --source "$source_export" --output "$staged_release" --commit "$sha" \
        --environment production --domain "$PRODUCTION_DOMAIN"
    rm -rf "$source_export"
    "$FINANCA_VERIFY_BIN" --artifact "$staged_release" --commit "$sha" \
        --environment production --domain "$PRODUCTION_DOMAIN"
    chown -R root:root "$staged_release"
    chmod -R go-w "$staged_release"
    mv "$staged_release" "$release"
fi
"$FINANCA_VERIFY_BIN" --artifact "$release" --commit "$sha" \
    --environment production --domain "$PRODUCTION_DOMAIN"

require_ga4=${REQUIRE_GA4:-true}
legacy_inventory="$release/deploy/odoo/financa_legacy.json"
[[ -f "$legacy_inventory" ]] || die "the release has no legacy content inventory: $legacy_inventory"
local_health="http://127.0.0.1:${ODOO_PORT}/web/login"
public_health="${PRODUCTION_DOMAIN}/web/login"
module_action=
recovery_point=
backup_created=false
activated=false
service_stopped=false

activate() {
    local target=$1 temporary="$releases/.current.$$.new"
    ln -s "$target" "$temporary"
    mv -Tf "$temporary" "$current"
}

run_odoo_shell() {
    local script=$1
    "${compose[@]}" run --rm --no-deps -T \
        -e FINANCA_DOMAIN="$PRODUCTION_DOMAIN" \
        -e REQUIRE_GA4="$require_ga4" \
        -e FINANCA_LEGACY_INVENTORY="$legacy_inventory" \
        odoo odoo shell -d "$ODOO_DB" < "$script"
}

detect_module_action() {
    local output
    output=$(run_odoo_shell "$release/deploy/odoo/module_state_financa.py")
    module_action=$(sed -n 's/^FINANCA_MODULE_ACTION=//p' <<< "$output")
    [[ "$module_action" == install || "$module_action" == update ]] \
        || die 'could not determine whether to install or update financa_website'
}

run_module_action() {
    if [[ $module_action == install ]]; then
        "${compose[@]}" run --rm --no-deps odoo \
            odoo -d "$ODOO_DB" -i financa_website --stop-after-init
    else
        "${compose[@]}" run --rm --no-deps odoo \
            odoo -d "$ODOO_DB" -u financa_website --stop-after-init
    fi
}

wait_for_health() {
    local url=$1
    for _ in {1..12}; do
        curl -fsS --max-time 10 -o /dev/null "$url" && return 0
        sleep 5
    done
    return 1
}

rollback() {
    local status=${1:-$?} recovered=true
    trap - ERR
    [[ $status -ne 0 ]] || return
    printf 'Deployment failed; restoring the previous production state.\n' >&2

    if [[ $service_stopped == true || $backup_created == true ]]; then
        "${compose[@]}" stop odoo || recovered=false
    fi
    if [[ $activated == true ]]; then
        activate "$previous" || recovered=false
    fi
    if [[ $backup_created == true ]]; then
        "$FINANCA_RESTORE_BIN" "$ODOO_DB" "$recovery_point" || recovered=false
    fi
    if [[ $recovered == true && ( $service_stopped == true || $backup_created == true ) ]]; then
        "${compose[@]}" up -d --force-recreate --no-deps odoo || recovered=false
        wait_for_health "$local_health" || recovered=false
        wait_for_health "$public_health" || recovered=false
    fi
    if [[ $recovered != true ]]; then
        "${compose[@]}" stop odoo || true
        printf 'RECOVERY FAILED: Odoo remains stopped for manual intervention.\n' >&2
    fi
    exit "$status"
}
trap rollback ERR

detect_module_action
run_odoo_shell "$release/deploy/odoo/preflight_financa.py"

"${compose[@]}" stop odoo
service_stopped=true
recovery_point=$("$FINANCA_BACKUP_BIN" "$ODOO_DB")
if [[ -z "$recovery_point" || "$recovery_point" == *$'\n'* \
    || ! "$recovery_point" =~ ^[A-Za-z0-9._:/-]+$ ]]; then
    printf 'PRODUCTION DEPLOY FAILED: backup hook did not return one valid recovery token\n' >&2
    rollback 1
fi
backup_created=true
printf 'Recovery point created: %s\n' "$recovery_point"

activate "$release"
activated=true
run_module_action
run_odoo_shell "$release/deploy/odoo/cleanup_financa_legacy.py"
run_odoo_shell "$release/deploy/odoo/configure_financa.py"
run_odoo_shell "$release/deploy/odoo/postflight_financa.py"
"${compose[@]}" up -d --force-recreate --no-deps odoo
service_stopped=false
if ! wait_for_health "$local_health"; then
    printf 'PRODUCTION DEPLOY FAILED: health check failed: %s\n' "$local_health" >&2
    rollback 1
fi
if ! wait_for_health "$public_health"; then
    printf 'PRODUCTION DEPLOY FAILED: health check failed: %s\n' "$public_health" >&2
    rollback 1
fi

trap - ERR
printf 'PRODUCTION DEPLOYED: %s (%s)\n' "$sha" "$module_action"
