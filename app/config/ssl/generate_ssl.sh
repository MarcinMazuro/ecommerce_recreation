#!/bin/bash
# Skrypt do generowania certyfikatu SSL dla PrestaShop

echo "=== Generowanie certyfikatu SSL dla PrestaShop ==="

CERT_FILE="prestashop.crt"
KEY_FILE="prestashop.key"

# Sprawdź czy certyfikat już istnieje
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "⚠️  Certyfikat SSL już istnieje!"
    read -p "Czy chcesz go nadpisać? (y/N): " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Anulowano. Używam istniejącego certyfikatu."
        exit 0
    fi
fi


# Generuj certyfikat
echo "Generuję certyfikat SSL (ważny 365 dni)..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=PL/ST=Poland/L=Warsaw/O=PrestaShop Dev/CN=localhost" \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Certyfikat SSL został wygenerowany pomyślnie!"
    echo "✓ Klucz prywatny: $KEY_FILE"
    echo "✓ Certyfikat: $CERT_FILE"
    echo ""
    echo "UWAGA: To jest certyfikat samopodpisany."
    echo "Przeglądarka wyświetli ostrzeżenie o bezpieczeństwie - to normalne."
else
    echo "✗ Błąd podczas generowania certyfikatu!"
    exit 1
fi
