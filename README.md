# E-commerce Recreation - Sklep DobreZiele.pl

Projekt odtworzenia sklepu internetowego DobreZiele.pl z wykorzystaniem platformy PrestaShop 1.7.8.

## 📋 Informacje o projekcie

**Wersja oprogramowania:** PrestaShop 1.7.8.8  
**Sklep źródłowy:** https://www.dobreziele.pl/  
**Repozytorium:** https://github.com/MarcinMazuro/ecommerce_recreation



## 📁 Struktura projektu

```
ecommerce_recreation/
├── app/
│   ├── config/          # Pliki konfiguracyjne i skrypty wdrożenia
│   │   ├── docker-compose.yml
│   │   ├── apache-ssl.conf
│   │   ├── ssl/         # Certyfikaty SSL
│   │   ├── export_database.sh    # Eksport bazy danych
│   │   ├── import_database.sh    # Import bazy danych
│   │   └── db-export/   # Eksporty bazy danych (.sql.gz)
│   ├── data/            # Rezultaty scrapowania (JSON UTF-8)
│   │   ├── categories.json
│   │   ├── products.json
│   │   └── products_with_details.json
│   ├── scraper/         # Skrypty do scrapowania
│   │   ├── category_scraper.py
│   │   ├── product_scraper.py
│   │   └── product_details_scraper.py
│   └── tests/           # Testy automatyczne Selenium
└── README.md
```

## 🚀 Uruchomienie projektu (dla członków zespołu)

### Wymagania wstępne

- Docker Desktop lub Docker Engine (z docker-compose)
- Git
- Python 3.8+ (dla skryptów scrapowania i testów)

### Pierwsze uruchomienie (nowy członek zespołu)

1. **Sklonuj repozytorium:**
```bash
git clone https://github.com/MarcinMazuro/ecommerce_recreation.git
cd ecommerce_recreation
```

2. **Wygeneruj certyfikat SSL:**
```bash
cd app/config
./generate_ssl.sh
```

3. **Uruchom kontenery Docker:**
```bash
docker compose up -d
```

4. **Otwórz sklep:**
   - **Sklep:** https://localhost:8443/
   - **Panel admina:** https://localhost:8443/admin475evahuy/

**UWAGA:** Certyfikat SSL jest samopodpisany - przeglądarka wyświetli ostrzeżenie. Kliknij "Zaawansowane" → "Przejdź do localhost:8443".

### Dane logowania

**Panel admina:**
- **Email:** admin@prestashop.local (lub inny użyty podczas instalacji)
- **Hasło:** [zapisane w zespole]

**Baza danych:**
- **Host:** db (wewnątrz Dockera)
- **Port:** 3306
- **Nazwa:** prestashop_db
- **User:** prestashop_user
- **Hasło:** secure_user_password

## 📊 Scrapowanie i import danych

### Instalacja zależności Python

```bash
pip install -r requirements.txt
```

### Pobieranie danych ze sklepu źródłowego

**1. Scrapowanie kategorii:**
```bash
cd app/scraper
python category_scraper.py
```

**2. Scrapowanie listy produktów:**
```bash
python product_scraper.py
```

**3. Scrapowanie szczegółów produktów:**
```bash
python product_details_scraper.py
```

Rezultaty zapisywane są w `app/data/` w formacie JSON z kodowaniem UTF-8.

### Import danych do PrestaShop przez API REST

**Konfiguracja Web Services w PrestaShop:**

1. Zaloguj się do panelu admina: `https://localhost:8443/admin475evahuy/`
2. Przejdź do: **Konfiguracja → Web Services (Usługi internetowe)**
3. Włącz opcję **"Włącz usługę Web Service PrestaShop"**
4. Przejdź do zakładki **"Klucze"** i kliknij **"Dodaj nowy klucz Web Service"**
5. Wypełnij formularz:
   - **Klucz:** zostanie wygenerowany automatycznie (skopiuj go!)
   - **Opis:** "Import produktów ze scrapowania"
   - **Status:** Włączony
   - **Uprawnienia:** zaznacz wszystkie (lub co najmniej: categories, products, images, stock_availables)
6. Zapisz klucz

**Uruchomienie importu:**

```bash
cd app/data

# Ustaw klucz API jako zmienną środowiskową
export PRESTASHOP_API_KEY="TWOJ_KLUCZ_API"

#Wyczysc dane jesli w bazie znajduja sie produkty lub kategorie
python clean_prestashop.py

# Uruchom import kategorii
python import_categories.py

# Uruchom import produktow
python import_products.py
```

Skrypt zaimportuje:
- Wszystkie kategorie i podkategorie ze scrapowania
- Produkty 
- Ceny, opisy, powiązania z kategoriami

**Uwaga:** Import dużej liczby produktów może zająć kilka minut (API ma ograniczenia prędkości).

## 🧪 Testy automatyczne Selenium

Testy znajdują się w katalogu `app/tests/` (w przygotowaniu).

```bash
cd app/tests
python test_shop.py
```

