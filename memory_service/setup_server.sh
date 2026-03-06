#!/bin/bash
set -e

DB_NAME="palantiri_db"
DB_USER="palantiri_user"
DB_PASSWORD=$(openssl rand -base64 32)
ENV_FILE="/etc/memory_service.env"

echo "==> Instalando PostgreSQL..."
sudo apt-get update -q
sudo apt-get install -y postgresql postgresql-contrib

echo "==> Iniciando PostgreSQL..."
sudo systemctl enable postgresql
sudo systemctl start postgresql

echo "==> Creando usuario y base de datos..."
sudo -u postgres psql <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;

CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
SQL

echo "==> Aplicando schema..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_TMP=$(mktemp)
cp "${SCRIPT_DIR}/schema.sql" "${SCHEMA_TMP}"
chmod 644 "${SCHEMA_TMP}"
sudo -u postgres psql -d "${DB_NAME}" -f "${SCHEMA_TMP}"
rm -f "${SCHEMA_TMP}"

sudo -u postgres psql -d "${DB_NAME}" <<SQL
GRANT ALL ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
SQL

echo "==> Guardando credenciales en ${ENV_FILE}..."
sudo tee "${ENV_FILE}" > /dev/null <<ENV
PGHOST=localhost
PGPORT=5432
PGUSER=${DB_USER}
PGPASSWORD=${DB_PASSWORD}
PGDATABASE=${DB_NAME}
ENV
sudo chmod 600 "${ENV_FILE}"

echo ""
echo "==> Setup completo."
echo "    Credenciales guardadas en: ${ENV_FILE}"
echo "    Anota la password para el cliente Python: ${DB_PASSWORD}"
