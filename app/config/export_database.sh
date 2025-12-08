#!/bin/bash
# Skrypt: app/config/export_database.sh

# Ustalenie nazwy pliku (np. dump_2023-12-08.sql)
FILENAME="db-export/dump_$(date +%F_%H-%M).sql"

echo "⏳ Trwa eksportowanie bazy danych do pliku: $FILENAME ..."

# Wykonanie zrzutu (dump) z kontenera bazy danych
docker compose exec db mysqldump -u prestashop_user -psecure_user_password prestashop_db > $FILENAME

echo "✅ Gotowe! Plik zapisano w: app/config/$FILENAME"