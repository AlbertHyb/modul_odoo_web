#!/usr/bin/env bash
set -Eeuo pipefail

readonly deploy_env=/etc/financa-production/deploy.env

die() {
    printf 'R2 RESTORE FAILED: %s\n' "$*" >&2
    exit 1
}

[[ ${EUID} -eq 0 ]] || die 'must run as root'
database=${1:?usage: financa-production-r2-restore <database> <token>}
token=${2:?usage: financa-production-r2-restore <database> <token>}
[[ "$database" =~ ^[A-Za-z0-9_]+$ ]] || die 'database name is invalid'
[[ "$token" =~ ^[A-Za-z0-9._-]+$ ]] || die 'recovery token is invalid'
[[ -f "$deploy_env" && ! -L "$deploy_env" ]] || die "missing $deploy_env"
# shellcheck disable=SC1090
source "$deploy_env"

for variable in COMPOSE_ENV_FILE COMPOSE_FILE R2_ENDPOINT R2_BUCKET R2_PREFIX R2_AWS_PROFILE; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $deploy_env"
done
[[ "$R2_PREFIX" =~ ^[A-Za-z0-9._/-]+$ && "$R2_PREFIX" != /* && "$R2_PREFIX" != */ ]] || die 'R2_PREFIX is invalid'

for command in aws docker grep mktemp rm sha256sum tar; do
    command -v "$command" >/dev/null || die "$command is required"
done
[[ -f "$COMPOSE_ENV_FILE" && -f "$COMPOSE_FILE" ]] || die 'Compose configuration is incomplete'
# shellcheck disable=SC1090
source "$COMPOSE_ENV_FILE"

for variable in POSTGRES_USER; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $COMPOSE_ENV_FILE"
done

compose=(docker compose --project-name odoo --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE")
"${compose[@]}" ps --status running --services | grep -Fxq odoo \
    && die 'odoo must be stopped before restore'
"${compose[@]}" exec -T db psql -U "$POSTGRES_USER" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname = '$database'" | grep -Fxq 1 \
    || die 'target database does not exist'

workdir=$(mktemp -d /var/tmp/financa-r2-restore.XXXXXX)
staged=".restore-$token"
previous=".previous-$token"
cleanup() {
    rm -rf -- "$workdir"
    "${compose[@]}" run --rm --no-deps -T --entrypoint sh odoo -c \
        'rm -rf -- "/var/lib/odoo/filestore/$1"' -- "$staged" >/dev/null 2>&1 || true
}
trap cleanup EXIT

base="s3://$R2_BUCKET/$R2_PREFIX/$token"
aws_args=(--profile "$R2_AWS_PROFILE" --endpoint-url "$R2_ENDPOINT")

for file in database.dump filestore.tar.gz database.name manifest.sha256; do
    aws "${aws_args[@]}" s3 cp "$base/$file" "$workdir/$file" --only-show-errors
done

[[ $(<"$workdir/database.name") == "$database" ]] || die 'recovery point is for another database'
(cd "$workdir" && sha256sum -c manifest.sha256)
tar -tzf "$workdir/filestore.tar.gz" > "$workdir/filestore.list"
grep -Fxq "$database/" "$workdir/filestore.list"

"${compose[@]}" run --rm --no-deps -T --entrypoint sh odoo -c '
    set -eu
    base=/var/lib/odoo/filestore
    staged="$base/$1"
    previous="$base/$3"
    test ! -e "$staged"
    test ! -e "$previous"
    mkdir "$staged"
    tar -C "$staged" -xzf -
    test -d "$staged/$2"
' -- "$staged" "$database" "$previous" < "$workdir/filestore.tar.gz"

"${compose[@]}" exec -T db \
    pg_restore -U "$POSTGRES_USER" --clean --if-exists -d "$database" < "$workdir/database.dump"

"${compose[@]}" run --rm --no-deps -T --entrypoint sh odoo -c '
    set -eu
    base=/var/lib/odoo/filestore
    staged="$base/$1"
    previous="$base/$2"
    database="$3"
    test ! -e "$previous"
    test -d "$staged/$database"
    test ! -e "$base/$database" || mv "$base/$database" "$previous"
    if ! mv "$staged/$database" "$base/$database"; then
        test ! -e "$base/$database" && test -e "$previous" && mv "$previous" "$base/$database" || true
        exit 1
    fi
    rm -rf -- "$previous" "$staged"
' -- "$staged" "$previous" "$database"
