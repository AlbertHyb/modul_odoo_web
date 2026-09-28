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

for command in aws docker grep mktemp mv rm sha256sum tar; do
    command -v "$command" >/dev/null || die "$command is required"
done
[[ -f "$COMPOSE_ENV_FILE" && -f "$COMPOSE_FILE" ]] || die 'Compose configuration is incomplete'
# shellcheck disable=SC1090
source "$COMPOSE_ENV_FILE"

for variable in POSTGRES_USER ODOO_DATA_DIR; do
    [[ -n ${!variable:-} ]] || die "missing $variable in $COMPOSE_ENV_FILE"
done

filestore="$ODOO_DATA_DIR/filestore/$database"
parent=${filestore%/*}
[[ -d "$parent" ]] || die "missing filestore parent: $parent"

workdir=$(mktemp -d /var/tmp/financa-r2-restore.XXXXXX)
staged_filestore=
trap 'rm -rf -- "$workdir" "${staged_filestore:-}"' EXIT

base="s3://$R2_BUCKET/$R2_PREFIX/$token"
aws_args=(--profile "$R2_AWS_PROFILE" --endpoint-url "$R2_ENDPOINT")

for file in database.dump filestore.tar.gz database.name manifest.sha256; do
    aws "${aws_args[@]}" s3 cp "$base/$file" "$workdir/$file" --only-show-errors
done

[[ $(<"$workdir/database.name") == "$database" ]] || die 'recovery point is for another database'
(cd "$workdir" && sha256sum -c manifest.sha256)
tar -tzf "$workdir/filestore.tar.gz" | grep -Fxq "$database/"

staged_filestore=$(mktemp -d "$parent/.${database}.restore.XXXXXX")
tar -C "$staged_filestore" -xzf "$workdir/filestore.tar.gz"
[[ -d "$staged_filestore/$database" ]] || die 'recovery point has no filestore'

docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
    pg_restore -U "$POSTGRES_USER" --clean --if-exists -d "$database" < "$workdir/database.dump"

previous_filestore="$parent/.${database}.previous.$token"
[[ ! -e "$previous_filestore" ]] || die "previous filestore path exists: $previous_filestore"

if [[ -e "$filestore" ]]; then
    mv "$filestore" "$previous_filestore"
fi
if ! mv "$staged_filestore/$database" "$filestore"; then
    [[ ! -e "$filestore" && -e "$previous_filestore" ]] && mv "$previous_filestore" "$filestore" || true
    die 'could not activate restored filestore'
fi

staged_filestore=
rm -rf -- "$previous_filestore"
