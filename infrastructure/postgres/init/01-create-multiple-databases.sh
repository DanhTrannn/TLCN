#!/bin/bash
set -eu

create_user_and_database() {
  local database=$1
  local user=${2:-$database}
  local password=${3:-password}
  echo "Creating user '$user' and database '$database'..."
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE USER $user WITH PASSWORD '$password';
    CREATE DATABASE $database OWNER $user;
    GRANT ALL PRIVILEGES ON DATABASE $database TO $user;
EOSQL
}

create_user_and_database polaris polaris "${POLARIS_DB_PASSWORD:-password}"
create_user_and_database airflow airflow "${AIRFLOW_DB_PASSWORD:-password}"
create_user_and_database superset superset "${SUPERSET_DB_PASSWORD:-password}"
