#!/bin/bash
# Skrypt: app/config/import_database.sh

# Sprawdzenie czy podano plik
if [ -z "$1" ]; then
    echo "❌ Błąd: Musisz podać nazwę pliku do importu."
    echo "Użycie: ./import_database.sh db-export/nazwa_pliku.sql"
    exit 1
fi

FILE=$1

if [ ! -f "$FILE" ]; then
    echo "❌ Błąd: Plik $FILE nie istnieje."
    exit 1
fi

echo "UWAGA: To polecenie NADPISZE całą obecną bazę danych!"
read -p "Czy na pewno chcesz kontynuować? (t/n): " confirm
if [[ $confirm != "t" && $confirm != "T" ]]; then
    echo "Anulowano."
    exit 0
fi

echo "Trwa importowanie bazy z pliku $FILE ..."

# Wczytanie pliku do kontenera bazy danych
cat $FILE | docker compose exec -T db mysql -u prestashop_user -psecure_user_password prestashop_db

echo "Sukces! Baza danych została przywrócona. Możliwe że trzeba jeszcze wyczyścić cashe"
