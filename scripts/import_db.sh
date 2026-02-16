#!/bin/bash
# scripts/import_db.sh

if [ -z "$1" ]; then
    echo "Usage: ./scripts/import_db.sh <path_to_dump_file.sql>"
    exit 1
fi

DUMP_FILE="$1"

if [ ! -f "$DUMP_FILE" ]; then
    echo "❌ Dump file not found: ${DUMP_FILE}"
    exit 1
fi

echo "Importing database from ${DUMP_FILE}..."
echo "WARNING: This will overwrite the existing 'killmatch' database."
read -p "Are you sure? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Drop and recreate the database to ensure a clean import
docker exec killmatch-postgres psql -U postgres -c "DROP DATABASE IF EXISTS killmatch;"
docker exec killmatch-postgres psql -U postgres -c "CREATE DATABASE killmatch;"

# Import the dump
cat "${DUMP_FILE}" | docker exec -i killmatch-postgres psql -U postgres -d killmatch

echo "✅ Database imported successfully!"
