#!/usr/bin/env bash
# Entorno de desarrollo de financa_website (Odoo 19 + PostgreSQL en Docker).
#   up      crea la base la primera vez y arranca Odoo
#   update  actualiza el módulo (después de cambiar Python, manifest o datos XML)
#   test    corre las pruebas del repositorio
#   logs    sigue el log de Odoo
#   stop    detiene los contenedores y libera la RAM (los datos se conservan)
#   reset   borra la base de desarrollo y sus archivos (pide confirmación)
set -Eeuo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd "$here/../.." && pwd)
db=financa_dev
port=${FINANCA_DEV_PORT:-8079}
compose=(docker compose -f "$here/compose.yaml")

odoo_once() {
    "${compose[@]}" run --rm --no-deps odoo odoo --config=/etc/odoo/odoo.conf -d "$db" --stop-after-init "$@"
}

psql_db() {
    "${compose[@]}" exec -T db psql -U odoo -d "$1" -tAc "$2"
}

db_ready() {
    [[ $(psql_db "$db" "select count(*) from ir_module_module where name = 'financa_website' and state = 'installed'" 2>/dev/null) == 1 ]]
}

wait_for_db() {
    for _ in $(seq 1 30); do
        "${compose[@]}" exec -T db pg_isready -U odoo -d postgres >/dev/null 2>&1 && return
        sleep 2
    done
    echo "PostgreSQL no respondió" >&2
    exit 1
}

bootstrap() {
    echo "Creando la base $db con website y CRM…"
    if [[ $(psql_db postgres "select 1 from pg_database where datname = '$db'") != 1 ]]; then
        odoo_once -i website,crm
    fi
    # El addon busca su sitio por el marcador __FINANCA_DOMAIN__ (el render lo cambia en staging/producción).
    # En desarrollo el único sitio lleva ese marcador; Odoo lo usa como sitio por defecto en cualquier host.
    psql_db "$db" "update website set name = 'Financa Consultores', domain = '__FINANCA_DOMAIN__' where id = (select min(id) from website)" >/dev/null
    psql_db "$db" "update res_company set email = 'desarrollo@financa.invalid' where id = 1 and coalesce(email, '') = ''" >/dev/null
    echo "Instalando financa_website…"
    odoo_once -i financa_website
}

case ${1:-up} in
    up)
        "${compose[@]}" up -d db
        wait_for_db
        db_ready || bootstrap
        "${compose[@]}" up -d odoo
        cat <<MSG

Odoo de desarrollo arriba en el VPS: 127.0.0.1:$port
Desde tu laptop:   ssh -N -L $port:localhost:$port <usuario>@<vps>
Luego abre:        http://localhost:$port   (admin / admin)
MSG
        ;;
    update)
        "${compose[@]}" stop odoo
        odoo_once -u financa_website
        "${compose[@]}" up -d odoo
        ;;
    test)
        cd "$repo" && python3 -m unittest discover -s tests
        ;;
    logs)
        "${compose[@]}" logs -f --tail=100 odoo
        ;;
    stop)
        "${compose[@]}" stop
        ;;
    reset)
        read -r -p "Se borrará la base $db y sus archivos. Escribe 'borrar' para continuar: " answer
        [[ $answer == borrar ]] || { echo "Cancelado."; exit 1; }
        "${compose[@]}" down -v
        ;;
    *)
        echo "Uso: $0 {up|update|test|logs|stop|reset}" >&2
        exit 2
        ;;
esac
