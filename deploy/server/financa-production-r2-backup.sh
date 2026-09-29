#!/usr/bin/env bash
set -Eeuo pipefail

readonly deploy_env=/etc/financa-production/deploy.env

die() {
    printf 'R2 BACKUP FAILED: %s\n' "$*" >&2
    exit 1
}

[[ ${EUID} -eq 0 ]] || die 'must run as root'
database=${1:?usage: financa-production-r2-backup <database>}
[[ -f "$deploy_env" && ! -L "$deploy_env" ]] || die "missing $deploy_env"
# shellcheck disable=SC1090
source "$deploy_env"

for variable in COMPOSE_ENV_FILE COMPOSE_FILE R2_ENDPOINT R2_BUCKET R2_PREFIX R2_AWS_PROFILE; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $deploy_env"
done
[[ "$database" =~ ^[A-Za-z0-9_]+$ ]] || die 'database name is invalid'
[[ "$R2_PREFIX" =~ ^[A-Za-z0-9._/-]+$ && "$R2_PREFIX" != /* && "$R2_PREFIX" != */ ]] || die 'R2_PREFIX is invalid'

for command in aws docker mktemp rm sha256sum tar; do
    command -v "$command" >/dev/null || die "$command is required"
done
[[ -f "$COMPOSE_ENV_FILE" && -f "$COMPOSE_FILE" ]] || die 'Compose configuration is incomplete'
# shellcheck disable=SC1090
source "$COMPOSE_ENV_FILE"

for variable in POSTGRES_USER; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $COMPOSE_ENV_FILE"
done

workdir=$(mktemp -d /var/tmp/financa-r2-backup.XXXXXX)
token=${workdir##*.}
trap 'rm -rf -- "$workdir"' EXIT

base="s3://$R2_BUCKET/$R2_PREFIX/$token"
aws_args=(--profile "$R2_AWS_PROFILE" --endpoint-url "$R2_ENDPOINT")

docker compose --project-name odoo --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
    pg_dump -U "$POSTGRES_USER" --format=custom "$database" > "$workdir/database.dump"
docker compose --project-name odoo --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" run --rm --no-deps -T \
    --entrypoint tar odoo -C /var/lib/odoo/filestore -czf - "$database" > "$workdir/filestore.tar.gz"
printf '%s\n' "$database" > "$workdir/database.name"
(cd "$workdir" && sha256sum database.dump filestore.tar.gz database.name > manifest.sha256)

aws "${aws_args[@]}" s3 cp "$workdir/database.dump" "$base/database.dump" --only-show-errors
aws "${aws_args[@]}" s3 cp "$workdir/filestore.tar.gz" "$base/filestore.tar.gz" --only-show-errors
aws "${aws_args[@]}" s3 cp "$workdir/database.name" "$base/database.name" --only-show-errors
aws "${aws_args[@]}" s3 cp "$workdir/manifest.sha256" "$base/manifest.sha256" --only-show-errors

printf '%s\n' "$token"
