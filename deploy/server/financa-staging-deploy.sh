#!/usr/bin/env bash
set -Eeuo pipefail

readonly repo=/srv/financa-staging/repo
readonly releases=/srv/financa-staging/releases
readonly current="$releases/current"
readonly local_health=http://127.0.0.1:8069/web/login
readonly public_health=https://staging.financa.mx/web/login

die() {
    printf 'STAGING DEPLOY FAILED: %s\n' "$*" >&2
    exit 1
}

[[ ${EUID} -eq 0 ]] || die 'must run as root'
[[ ${SSH_ORIGINAL_COMMAND:-} =~ ^deploy\ ([0-9a-f]{40})$ ]] \
    || die 'only deploy <40-char-staging-sha> is allowed'
sha=${BASH_REMATCH[1]}
[[ -d "$repo/.git" && -f "$repo/deploy/compose/.env" ]] || die 'staging checkout is incomplete'

exec 9>/run/lock/financa-staging-deploy.lock
flock -n 9 || die 'another staging deployment is running'

compose=(docker compose --env-file "$repo/deploy/compose/.env" -f "$repo/deploy/compose/compose.yaml")
previous=$(readlink -f "$current")
[[ -d "$previous" ]] || die 'current release is invalid'
activated=false
module_update_started=false

activate() {
    local target=$1 temporary="$releases/.current.$$.new"
    ln -s "$target" "$temporary"
    mv -Tf "$temporary" "$current"
}

rollback() {
    local status=$?
    trap - ERR
    [[ $status -ne 0 ]] || return
    if [[ $activated == true ]]; then
        printf 'Restoring the prior release symlink.\n' >&2
        activate "$previous" || true
        "${compose[@]}" up -d --force-recreate --no-deps odoo || true
    fi
    if [[ $module_update_started == true ]]; then
        printf 'A fresh R2 backup exists; review the database before any manual restore.\n' >&2
    fi
    exit "$status"
}
trap rollback ERR

runuser -u ubuntu -- git -C "$repo" fetch --quiet origin staging
[[ $(runuser -u ubuntu -- git -C "$repo" rev-parse origin/staging) == "$sha" ]] \
    || die 'requested SHA is not the current origin/staging tip'
runuser -u ubuntu -- git -C "$repo" checkout --detach --quiet "$sha"

release="$releases/$sha"
if [[ ! -e "$release" ]]; then
    runuser -u ubuntu -- python3 "$repo/deploy/ci/render_financa_staging_artifact.py" \
        --source "$repo" --output "$release" --commit "$sha" --domain https://staging.financa.mx
fi
[[ -f "$release/artifact-manifest.json" ]] || die 'rendered release has no manifest'
grep -Fq "\"commit\": \"$sha\"" "$release/artifact-manifest.json" \
    || die 'release manifest does not match the requested SHA'

systemctl start --wait financa-staging-backup.service
activate "$release"
activated=true
"${compose[@]}" stop odoo
module_update_started=true
"${compose[@]}" run --rm --no-deps odoo \
    odoo -d financa_staging -u financa_website --stop-after-init
"${compose[@]}" up -d --force-recreate --no-deps odoo

wait_for_health() {
    local url=$1
    for _ in {1..12}; do
        curl -fsS --max-time 10 -o /dev/null "$url" && return 0
        sleep 5
    done
    die "health check failed: $url"
}
wait_for_health "$local_health"
wait_for_health "$public_health"
trap - ERR
printf 'STAGING DEPLOYED: %s\n' "$sha"
