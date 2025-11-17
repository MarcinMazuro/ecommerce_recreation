import requests
import json
import xml.etree.ElementTree as ET
from slugify import slugify
import sys
import warnings
# --- KONFIGURACJA ---
PRESTASHOP_URL = 'https://localhost:8443/api' # Użyj portu 8443 jeśli masz HTTPS
API_KEY = '9HI4BPPVSZCVULACXFQUYMABJUE74X5V' # Wklej klucz z Panelu Admina
INPUT_FILE = 'categories.json' 
ID_KATEGORII_GLOWNEJ = 2 # Domyślny ID kategorii "Home" w PrestaShop

# Globalna mapa do przechowywania już utworzonych kategorii, aby uniknąć duplikatów
# Klucz: (nazwa, id_rodzica), Wartość: id_kategorii
created_categories = {}

session = requests.Session()
session.auth = (API_KEY, '')
session.verify = False # <-- DODAJ TĘ LINIĘ

# Ta linia wyłączy denerwujące ostrzeżenia o "niezaufanym" połączeniu
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# --- FUNKCJE POMOCNICZE API ---

def get_api_xml(endpoint, options=None):
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        response = session.get(url, params=options)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Błąd GET {url}: {e}\nOdpowiedź: {e.response.content.decode()}", file=sys.stderr)
        return None

def post_api_xml(endpoint, xml_data):
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        headers = {'Content-Type': 'application/xml'}
        response = session.post(url, data=xml_data.encode('utf-8'))
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Błąd POST {url}: {e}\nOdpowiedź: {e.response.content.decode()}", file=sys.stderr)
        return None

def get_or_create_category(name, parent_id):
    """Sprawdza lub tworzy kategorię i zwraca jej ID."""
    cache_key = (name, parent_id)
    if cache_key in created_categories:
        return created_categories[cache_key]

    options = {'filter[name]': name, 'filter[id_parent]': parent_id, 'display': 'full'}
    xml = get_api_xml('categories', options)
    
    if xml is not None and xml.find('.//category') is not None:
        category_id = xml.find('.//category/id').text
        print(f"  Kategoria '{name}' już istnieje (ID: {category_id}).")
        created_categories[cache_key] = category_id
        return category_id
    
    print(f"  Tworzenie kategorii: '{name}' (Rodzic ID: {parent_id})")
    
    xml_data = f"""
    <prestashop>
      <category>
        <active>1</active>
        <id_parent>{parent_id}</id_parent>
        <name><language id="1"><![CDATA[{name}]]></language></name>
        <link_rewrite><language id="1"><![CDATA[{slugify(name)}]]></language></link_rewrite>
      </category>
    </prestashop>
    """
    
    new_xml = post_api_xml('categories', xml_data)
    
    if new_xml is not None:
        new_category_id = new_xml.find('.//category/id').text
        print(f"  Utworzono kategorię (ID: {new_category_id})")
        created_categories[cache_key] = new_category_id
        return new_category_id
    else:
        print(f"  BŁĄD: Nie udało się utworzyć kategorii '{name}'")
        return None

# --- FUNKCJA REKURENCYJNA ---

def process_categories_recursively(category_list, parent_id):
    """Rekursywnie przetwarza listę kategorii."""
    if not category_list:
        return

    for category_data in category_list:
        name = category_data.get('name')
        if not name:
            continue
            
        new_category_id = get_or_create_category(name, parent_id)
        
        if new_category_id:
            subcategories = category_data.get('subcategories')
            if subcategories:
                process_categories_recursively(subcategories, new_category_id)

# --- GŁÓWNA FUNKCJA ---

def main():
    print(f"Rozpoczynanie importu drzewa kategorii z pliku: {INPUT_FILE}")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku {INPUT_FILE}", file=sys.stderr)
        return
    except json.JSONDecodeError:
        print(f"BŁĄD: Plik {INPUT_FILE} nie jest poprawnym plikiem JSON.", file=sys.stderr)
        return

    print(f"Przetwarzanie kategorii głównych (Rodzic: {ID_KATEGORII_GLOWNEJ})...")
    process_categories_recursively(categories_data, ID_KATEGORII_GLOWNEJ)
    print("\n--- Zakończono import kategorii ---")

if __name__ == "__main__":
    main()