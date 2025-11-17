import requests
import json
import xml.etree.ElementTree as ET
import re
from slugify import slugify
import sys
import io

# --- KONFIGURACJA ---
PRESTASHOP_URL = 'https://localhost:8443/api' # Użyj portu 8443 jeśli masz HTTPS
API_KEY = '9HI4BPPVSZCVULACXFQUYMABJUE74X5V' # Ten sam klucz co w skrypcie 1
INPUT_FILE = 'products_with_details.json' # Plik z listą produktów
DOMYSLNA_ILOSC = 9 # Zgodnie z wymogiem < 10

session = requests.Session()
session.auth = (API_KEY, '')
session.auth = (API_KEY, '')
session.verify = False # <-- DODAJ TĘ LINIĘ

# Mapy cache, aby nie pytać API o to samo
manufacturers_cache = {}
categories_cache = {}

# --- FUNKCJE POMOCNICZE API (Skopiowane ze skryptu 1) ---

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

def put_api_xml(endpoint, xml_data):
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        headers = {'Content-Type': 'application/xml'}
        # ET.tostring zwraca bajty, nie trzeba kodować
        response = session.put(url, data=xml_data) 
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Błąd PUT {url}: {e}\nOdpowiedź: {e.response.content.decode()}", file=sys.stderr)
        return False

# --- FUNKCJE POMOCNICZE DANYCH ---

def clean_price(price_str):
    """Przekształca '31.00 zł' na '31.00'."""
    if not price_str: return "0.00"
    price = re.sub(r'[^\d.]', '', price_str.replace(',', '.'))
    return f"{float(price):.2f}" if price else "0.00"

def format_html(text):
    """Zmienia nowe linie na tagi <p> dla opisów PrestaShop."""
    if not text: return ""
    paragraphs = text.split('\n')
    return "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

# --- FUNKCJE "ZNAJDŹ LUB UTWÓRZ" ---

def get_or_create_manufacturer(name):
    if not name: return '0'
    if name in manufacturers_cache: return manufacturers_cache[name]
    
    print(f"  Producent: {name}")
    options = {'filter[name]': name, 'display': 'full'}
    xml = get_api_xml('manufacturers', options)
    
    if xml is not None and xml.find('.//manufacturer') is not None:
        id = xml.find('.//manufacturer/id').text
        manufacturers_cache[name] = id
        return id
    
    print(f"    Tworzenie producenta: {name}")
    xml_data = f"""<prestashop><manufacturer>
        <active>1</active>
        <name>{name}</name>
        <link_rewrite>{slugify(name)}</link_rewrite> 
    </manufacturer></prestashop>"""
    new_xml = post_api_xml('manufacturers', xml_data)
    if new_xml is None:
        print(f"    BŁĄD: Nie udało się utworzyć producenta", file=sys.stderr)
        return '0'
    id = new_xml.find('.//manufacturer/id').text
    manufacturers_cache[name] = id
    return id

def get_category_id_by_path(path_str):
    """Znajduje ID kategorii na podstawie ścieżki "Kat1/Kat2"."""
    print(f"  Kategorie: {path_str}")
    parent_id = 2 # Zaczynamy od "Home"
    
    if not path_str: return parent_id, [parent_id]
        
    parts = [p.strip() for p in path_str.split('/')]
    all_ids = {parent_id}
    
    for part in parts:
        cache_key = (part, parent_id)
        if cache_key in categories_cache:
            parent_id = categories_cache[cache_key]
        else:
            options = {'filter[name]': part, 'filter[id_parent]': parent_id, 'display': 'full'}
            xml = get_api_xml('categories', options)
            
            if xml is not None and xml.find('.//category') is not None:
                parent_id = xml.find('.//category/id').text
                categories_cache[cache_key] = parent_id
            else:
                # Kategoria powinna być utworzona przez Skrypt 1, ale na wszelki wypadek...
                print(f"    Ostrzeżenie: Nie znaleziono kategorii '{part}' w rodzicu {parent_id}.")
                # Zwracamy ostatnie znane ID
                return parent_id, list(all_ids)
        
        all_ids.add(parent_id)
            
    return parent_id, list(all_ids) # Zwraca ID ostatniej kategorii i listę wszystkich ID


# --- FUNKCJE PRODUKTU ---

def set_stock(product_id, quantity=DOMYSLNA_ILOSC):
    print(f"  Ustawianie stanu magazynowego ({quantity} szt.)")
    options = {'filter[id_product]': product_id, 'display': 'full'}
    xml = get_api_xml('stock_availables', options)
    
    if xml is None or xml.find('.//stock_available') is None:
        print(f"    Błąd: Nie znaleziono 'stock_available' dla produktu {product_id}")
        return

    stock_id = xml.find('.//stock_available/id').text
    stock_xml = get_api_xml(f'stock_availables/{stock_id}')
    
    if stock_xml is None: return

    stock_xml.find('.//quantity').text = str(quantity)
    
    # Usuwamy pola tylko do odczytu
    for field in ['id_product_attribute', 'depends_on_stock', 'out_of_stock', 'shop_name']:
        elem = stock_xml.find(f'.//{field}')
        if elem is not None:
            stock_xml.find('.').remove(elem)

    put_api_xml(f'stock_availables/{stock_id}', ET.tostring(stock_xml))

def upload_image(product_id, image_url):
    print(f"  Pobieranie obrazu: {image_url}")
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        files = {'image': (f'product_{product_id}.jpg', response.content, 'image/jpeg')}
        url = f"{PRESTASHOP_URL}/images/products/{product_id}"
        
        upload_response = session.post(url, files=files)
        upload_response.raise_for_status()
        print("    Obraz wgrany pomyślnie.")
    except requests.exceptions.RequestException as e:
        print(f"    Błąd wgrywania obrazu: {e}", file=sys.stderr)

# --- GŁÓWNA FUNKCJA ---

def main():
    print("Rozpoczynanie importu produktów...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku {INPUT_FILE}", file=sys.stderr)
        return
    
    for i, item in enumerate(data):
        details = item.get('szczegoly_produktu', {})
        if not details:
            continue
            
        name = item.get('nazwa')
        print(f"\n--- Przetwarzanie produktu {i+1}/{len(data)}: {name} ---")
        
        # 1. Sprawdź, czy produkt już istnieje
        options = {'filter[name]': name, 'display': 'full'}
        xml = get_api_xml('products', options)
        if xml is not None and xml.find('.//product') is not None:
            print("  Produkt już istnieje. Pomijanie.")
            continue

        # 2. Zbierz dane
        # Cena w JSON to cena BRUTTO - PrestaShop potrzebuje NETTO (podziel przez 1.23)
        cena_brutto = float(clean_price(details.get('cena', '0.00')))
        price = f"{(cena_brutto / 1.23):.2f}"  # Przelicz na netto
        
        # Opis + szczegóły produktu
        description = format_html(details.get('opis', ''))
        szczegoly = details.get('szczegoly', {})
        if szczegoly:
            description += "\n<h3>Szczegóły produktu:</h3>\n<ul>\n"
            for key, value in szczegoly.items():
                if value:
                    description += f"<li><strong>{key}:</strong> {value}</li>\n"
            description += "</ul>"
        manufacturer_id = get_or_create_manufacturer(details.get('marka'))
        
        # 3. Kategorie
        default_category_id, category_ids = get_category_id_by_path(item.get('kategoria_pelna_sciezka', ''))
        categories_xml = "".join(f"<category><id>{cid}</id></category>" for cid in category_ids)

        # 4. Przygotuj pole manufacturer (tylko jeśli marka istnieje)
        manufacturer_xml = f"<id_manufacturer>{manufacturer_id}</id_manufacturer>" if manufacturer_id != '0' else ""
        
        # 5. Zbuduj XML produktu (łącząc wszystko)
        product_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
<product>
    <name><language id="1"><![CDATA[{name}]]></language></name>
    <link_rewrite><language id="1"><![CDATA[{slugify(name)}]]></language></link_rewrite>
    <description><language id="1"><![CDATA[{description}]]></language></description>
    <description_short><language id="1"><![CDATA[{description[:150]}]]></language></description_short>
    {manufacturer_xml}
    <id_category_default>{default_category_id}</id_category_default>
    <price>{price}</price>
    <id_tax_rules_group>1</id_tax_rules_group>
    <active>1</active>
    <available_for_order>1</available_for_order>
    <show_price>1</show_price>
    <state>1</state>
    <minimal_quantity>1</minimal_quantity>
    <id_shop_default>1</id_shop_default>
    <associations>
        <categories>{categories_xml}</categories>
    </associations>
</product>
</prestashop>"""
        
        # 6. Utwórz produkt
        print("  Tworzenie produktu...")
        new_product_xml = post_api_xml('products', product_xml)
        if new_product_xml is None:
            print(f"BŁĄD: Nie udało się utworzyć produktu {name}", file=sys.stderr)
            continue
            
        product_id = new_product_xml.find('.//product/id').text
        print(f"  Utworzono produkt. ID: {product_id}")

        # 7. Ustaw stan magazynowy
        set_stock(product_id)

        # 8. Wgraj zdjęcia
        for img_url in details.get('zdjecia', []):
            upload_image(product_id, img_url)

    print("\n--- Zakończono import produktów ---")

if __name__ == "__main__":
    main()