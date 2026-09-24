#!/usr/bin/env bash
# Run from any CI runner with OpenSSH, python3, tar, and a checked-out repository.
set -Eeuo pipefail

die() {
    printf 'PUBLISH FAILED: %s\n' "$*" >&2
    exit 1
}

for variable in DEPLOY_HOST DEPLOY_USER DEPLOY_SSH_KEY DEPLOY_KNOWN_HOSTS DEPLOY_DOMAIN; do
    [[ -n ${!variable:-} ]] || die "missing CI variable: $variable"
done
[[ -f "$DEPLOY_SSH_KEY" ]] || die "DEPLOY_SSH_KEY must point to a private-key file"
[[ -f "$DEPLOY_KNOWN_HOSTS" ]] || die "DEPLOY_KNOWN_HOSTS must point to a known_hosts file"
[[ -d financa_website && -d deploy/odoo ]] || die "run from repository root"
command -v python3 >/dev/null || die "python3 is required to render the artifact"

deploy_port=${DEPLOY_PORT:-22}
deploy_root=${DEPLOY_REMOTE_ROOT:-/var/tmp/financa-deploy}
revision=${CI_COMMIT_SHA:-${GITHUB_SHA:-$(git rev-parse --short HEAD)}}
run_id=${CI_PIPELINE_ID:-${GITHUB_RUN_ID:-$(date +%Y%m%d%H%M%S)}}
deployment_id="${run_id}-${revision}"
[[ "$deployment_id" =~ ^[A-Za-z0-9._-]+$ ]] || die "deployment identifier contains unsupported characters"
[[ "$deploy_root" == /* && "$deploy_root" != *" "* ]] || die "DEPLOY_REMOTE_ROOT must be an absolute path without spaces"

remote_target="${DEPLOY_USER}@${DEPLOY_HOST}"
remote_stage="${deploy_root%/}/${deployment_id}"
remote_archive="${remote_stage}/financa_website.tgz"
render_root=$(mktemp -d "${TMPDIR:-/tmp}/financa-render.XXXXXX")
artifact="${render_root}/artifact"
local_archive=$(mktemp "${TMPDIR:-/tmp}/financa_website.XXXXXX.tgz")
cleanup() {
    rm -rf "$render_root"
    rm -f "$local_archive"
}
trap cleanup EXIT

ssh_options=(
    -i "$DEPLOY_SSH_KEY"
    -p "$deploy_port"
    -o BatchMode=yes
    -o StrictHostKeyChecking=yes
    -o "UserKnownHostsFile=$DEPLOY_KNOWN_HOSTS"
)

scp_options=(
    -i "$DEPLOY_SSH_KEY"
    -P "$deploy_port"
    -o BatchMode=yes
    -o StrictHostKeyChecking=yes
    -o "UserKnownHostsFile=$DEPLOY_KNOWN_HOSTS"
)

# The repository ships the __FINANCA_DOMAIN__ token, so the production hostname
# only enters the pipeline here. The server preflight aborts when the resulting
# artifact and /etc/financa/deploy.env disagree about that hostname.
python3 deploy/ci/render_financa_artifact.py \
    --source . \
    --output "$artifact" \
    --commit "$revision" \
    --environment production \
    --domain "$DEPLOY_DOMAIN"

tar --exclude='__pycache__' --exclude='*.pyc' -C "$artifact" -czf "$local_archive" \
    financa_website deploy/odoo artifact-manifest.json
ssh "${ssh_options[@]}" "$remote_target" "install -d -m 0750 $(printf '%q' "$remote_stage")"
scp "${scp_options[@]}" "$local_archive" "${remote_target}:${remote_archive}"
ssh "${ssh_options[@]}" "$remote_target" \
    "tar -xzf $(printf '%q' "$remote_archive") -C $(printf '%q' "$remote_stage") && sudo -n /usr/local/sbin/financa-deploy $(printf '%q' "$remote_stage/financa_website") $(printf '%q' "$remote_stage/deploy/odoo")"

printf 'Published revision %s for %s to %s\n' "$revision" "$DEPLOY_DOMAIN" "$remote_target"

