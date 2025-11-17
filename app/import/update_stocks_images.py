import json
import xml.etree.ElementTree as ET
import os
import sys
from pathlib import Path
import random
from prestashop_api import get_api_xml, put_api_xml, post_image

INPUT_FILE = '../data/products_with_details.json'
IMAGES_DIR = '../data/images'


def sanitize_filename(name):
    """Sanityzuje nazwę do formatu używanego w nazwach folderów."""
    import re
    name = name.replace(' ', '_')
    name = re.sub(r'[^\w\-]', '', name)
    return name

STOCK_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <stock_available>
    <id><![CDATA[{stock_id}]]></id>
    <id_product><![CDATA[{product_id}]]></id_product>
    <id_product_attribute><![CDATA[0]]></id_product_attribute>
    <id_shop><![CDATA[1]]></id_shop>
    <quantity><![CDATA[{quantity}]]></quantity>
    <depends_on_stock><![CDATA[0]]></depends_on_stock>
    <out_of_stock><![CDATA[2]]></out_of_stock>
  </stock_available>
</prestashop>"""

def set_stock(product_id):
    quantity = random.randint(1, 9)
    """Ustawia stan magazynowy produktu przy użyciu czystego szablonu XML."""
    print(f"  Ustawianie stanu magazynowego ({quantity} szt.)")
    
    # 1. Znajdź ID stanu magazynowego dla produktu (tylko ID)
    options = {'filter[id_product]': product_id, 'display': '[id]'}
    xml_list = get_api_xml('stock_availables', options)
    
    if xml_list is None or xml_list.find('.//stock_available') is None:
        print(f"    Błąd: Nie znaleziono 'stock_available' dla produktu {product_id}")
        return False

    stock_id = xml_list.find('.//stock_available/id').text
    
    # 2. Zbuduj XML z szablonu
    xml_data = STOCK_TEMPLATE.format(
        stock_id=stock_id,
        product_id=product_id,
        quantity=quantity
    )
    
    # 3. Wyślij zaktualizowany XML
    return put_api_xml(f'stock_availables/{stock_id}', xml_data)
# --- GŁÓWNA FUNKCJA ---

def main():
    print("Rozpoczynanie aktualizacji stanów magazynowych i zdjęć...")
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"BŁĄD: Nie znaleziono pliku {INPUT_FILE}", file=sys.stderr)
        return
    
    # Pobierz wszystkie produkty z PrestaShop raz na początku
    print("Pobieranie listy wszystkich produktów z PrestaShop...")
    all_products_xml = get_api_xml('products', {'display': '[id,name]'})
    
    if all_products_xml is None:
        print("BŁĄD: Nie udało się pobrać listy produktów", file=sys.stderr)
        return
    
    # Zbuduj mapę nazwa -> id produktu
    products_map = {}
    for product in all_products_xml.findall('.//product'):
        prod_id = product.find('id').text
        prod_name_elem = product.find('.//language')
        if prod_name_elem is not None:
            prod_name = prod_name_elem.text
            products_map[prod_name] = prod_id
    
    print(f"Znaleziono {len(products_map)} produktów w PrestaShop")
    images_uploaded = 0
    for i, item in enumerate(data):
        name = item.get('nazwa')
        if not name:
            continue
            
        print(f"\n--- Przetwarzanie produktu {i+1}/{len(data)}: {name} ---")
        
        # 1. Znajdź produkt w mapie
        product_id = products_map.get(name)
        
        if not product_id:
            print("  Produkt nie istnieje w PrestaShop. Pomijanie.")
            continue
        
        print(f"  Znaleziono produkt. ID: {product_id}")
        
        # 2. Ustaw stan magazynowy
        print(f"  Ustawianie stanu magazynowego na losowa wartosc...")
        if set_stock(product_id):
            print("    ✓ Stan magazynowy ustawiony")
        else:
           print("    ✗ Błąd ustawiania stanu magazynowego")
        
        # 3. Wgraj zdjęcie z lokalnego dysku
        product_id_from_json = item.get('id_produktu', '')
        
        # Prosta ścieżka: images/id_nazwa/product.jpg
        if product_id_from_json:
            product_folder = f"{product_id_from_json}_{sanitize_filename(name)}"
            image_path = f"{IMAGES_DIR}/{product_folder}/product.jpg"
  
            if os.path.exists(image_path):
                print(f"  Wgrywanie zdjęcia: {image_path}")
                if post_image(product_id, image_path):
                    print("    ✓ Zdjęcie wgrane")
                    images_uploaded += 1
                else:
                    print("    ✗ Błąd wgrywania zdjęcia")
            else:
                print(f"    Nie znaleziono zdjęcia: {image_path}")

    print("\n--- Zakończono aktualizację ---")
    print(f"Łącznie wgrano zdjęć: {images_uploaded}")
if __name__ == "__main__":
    main()
