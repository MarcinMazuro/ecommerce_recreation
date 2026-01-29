#!/bin/bash
set -e

# Pobierz dane z ENV (dla klastra lub lokalnie)
DB_HOST="${DB_SERVER:-db}"
DB_NAME="${DB_NAME:-BE_198019}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASSWD:-student}"

echo "=== PrestaShop Auto-Init ==="
echo "DB Host: $DB_HOST"
echo "DB Name: $DB_NAME"
echo "DB User: $DB_USER"

# 1. Czekaj na bazę danych
echo "Czekam na bazę danych $DB_HOST..."
MAX_TRIES=60
TRIES=0
until mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "SELECT 1" > /dev/null 2>&1; do
    TRIES=$((TRIES + 1))
    if [ $TRIES -ge $MAX_TRIES ]; then
        echo "BŁĄD: Nie można połączyć się z bazą danych!"
        exit 1
    fi
    echo "  Próba $TRIES/$MAX_TRIES..."
    sleep 2
done
echo "✓ Połączono z bazą danych"

# 2. Utwórz bazę jeśli nie istnieje
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;" 2>/dev/null || true

# 3. Sprawdź czy baza jest pusta i zaimportuj
TABLES=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SHOW TABLES;" 2>/dev/null | wc -l)

if [ "$TABLES" -le 1 ]; then
    echo "Baza pusta - importuję dump..."
    if [ -f /seed/prestashop.sql ]; then
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < /seed/prestashop.sql
        echo "✓ Import bazy zakończony"
    else
        echo "UWAGA: Brak pliku /seed/prestashop.sql"
    fi
else
    echo "Baza zawiera $((TABLES - 1)) tabel - pomijam import"
fi

# 4. Wyczyść cache PrestaShop
echo "Czyszczenie cache..."
rm -rf /var/www/html/var/cache/* 2>/dev/null || true
rm -rf /var/www/html/cache/* 2>/dev/null || true

# 5. Napraw uprawnienia
echo "Ustawiam uprawnienia..."
chown -R www-data:www-data /var/www/html/var 2>/dev/null || true
chown -R www-data:www-data /var/www/html/img 2>/dev/null || true
chown -R www-data:www-data /var/www/html/cache 2>/dev/null || true
chmod -R 755 /var/www/html/var 2>/dev/null || true
chmod -R 755 /var/www/html/img 2>/dev/null || true

echo "✓ Inicjalizacja zakończona"
echo "=== Uruchamiam Apache ==="
exec "$@"