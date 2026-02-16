#!/bin/bash
# scripts/export_db.sh

# Ensure the dump directory exists
mkdir -p db_dumps

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DUMP_FILE="db_dumps/killmatch_dump_${TIMESTAMP}.sql"

echo "Exporting 'killmatch' database to ${DUMP_FILE}..."

if docker exec killmatch-postgres pg_dump -U postgres killmatch > "${DUMP_FILE}"; then
    echo "✅ Database exported successfully!"
    echo "Share this file with your teammate."
else
    echo "❌ Database export failed."
    exit 1
fi
