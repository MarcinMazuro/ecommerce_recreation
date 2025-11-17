import json
import xml.etree.ElementTree as ET
import re
from slugify import slugify
import sys
from prestashop_api import get_api_xml, post_api_xml, put_api_xml

INPUT_FILE = '../data/products_with_details.json'

manufacturers_cache = {}
categories_cache = {}
features_cache = {}
feature_values_cache = {}


def clean_price(price_str):
    """Przekształca '31.00 zł' na '31.00'."""
    if not price_str: return "0.00"
    price = re.sub(r'[^\d.]', '', price_str.replace(',', '.'))
    return f"{float(price):.2f}" if price else "0.00"

def format_html(text):
    """Formatuje tekst z \n na HTML. Słowa przed \n są pogrubiane."""
    if not text: return ""
    
    text = re.sub(r'([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]+)\n([a-ząćęłńóśźż])', r'<strong>\1</strong>\n\2', text)
    
    text = text.replace('\n\n', '|||PARAGRAPH|||')
    text = text.replace('\n', ' ')
    text = text.replace('|||PARAGRAPH|||', '</p><p>')
    
    # Dodaj <br> przed każdym pogrubieniem (oprócz pierwszego)
    text = re.sub(r'([a-ząćęłńóśźż\.]) <strong>', r'\1<br><strong>', text)
    
    return f"<p>{text}</p>"


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
        <name><![CDATA[{name}]]></name>
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
                print(f"    Ostrzeżenie: Nie znaleziono kategorii '{part}' w rodzicu {parent_id}.")
                return parent_id, list(all_ids)
        
        all_ids.add(parent_id)
            
    return parent_id, list(all_ids) # Zwraca ID ostatniej kategorii i listę wszystkich ID


def get_or_create_feature(name):
    """Znajduje lub tworzy cechę (feature) po nazwie."""
    if name in features_cache:
        return features_cache[name]
    
    options = {'filter[name]': name, 'display': 'full'}
    xml = get_api_xml('product_features', options)
    
    if xml is not None and xml.find('.//product_feature') is not None:
        feature_id = xml.find('.//product_feature/id').text
        features_cache[name] = feature_id
        return feature_id
    
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
<product_feature>
    <name><language id="1"><![CDATA[{name}]]></language></name>
</product_feature>
</prestashop>"""
    
    new_xml = post_api_xml('product_features', xml_data)
    if new_xml is None:
        return None
    
    feature_id = new_xml.find('.//product_feature/id').text
    features_cache[name] = feature_id
    return feature_id


def get_or_create_feature_value(feature_id, value):
    """Znajduje lub tworzy wartość cechy (feature value)."""
    cache_key = (feature_id, value)
    if cache_key in feature_values_cache:
        return feature_values_cache[cache_key]
    
    options = {'filter[id_feature]': feature_id, 'filter[value]': value, 'display': 'full'}
    xml = get_api_xml('product_feature_values', options)
    
    if xml is not None and xml.find('.//product_feature_value') is not None:
        value_id = xml.find('.//product_feature_value/id').text
        feature_values_cache[cache_key] = value_id
        return value_id
    
    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
<product_feature_value>
    <id_feature>{feature_id}</id_feature>
    <value><language id="1"><![CDATA[{value}]]></language></value>
</product_feature_value>
</prestashop>"""
    
    new_xml = post_api_xml('product_feature_values', xml_data)
    if new_xml is None:
        return None
    
    value_id = new_xml.find('.//product_feature_value/id').text
    feature_values_cache[cache_key] = value_id
    return value_id



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

        # 4. Przygotuj cechy produktu (features)
        print("  Tworzenie cech produktu...")
        features_xml = ""
        if szczegoly:
            feature_items = []
            for key, value in szczegoly.items():
                if value:
                    feature_id = get_or_create_feature(key)
                    if feature_id:
                        value_id = get_or_create_feature_value(feature_id, value)
                        if value_id:
                            feature_items.append(f"<product_feature><id>{feature_id}</id><id_feature_value>{value_id}</id_feature_value></product_feature>")
            
            if feature_items:
                features_xml = "".join(feature_items)

        # 5. Przygotuj pole manufacturer (tylko jeśli marka istnieje)
        manufacturer_xml = f"<id_manufacturer>{manufacturer_id}</id_manufacturer>" if manufacturer_id != '0' else ""
        
        # 6. Zbuduj XML produktu (łącząc wszystko)
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
        <product_features>{features_xml}</product_features>
    </associations>
</product>
</prestashop>"""
        
        # 6. Utwórz produkt
        print("  Tworzenie produktu...")
        new_product_xml = post_api_xml('products', product_xml)
        if new_product_xml is None:
            print(f"BŁĄD: Nie udało się utworzyć produktu {name}", file=sys.stderr)
            continue
            

    print("\n--- Zakończono import produktów ---")
    print("Uruchom teraz skrypt update_stocks_images.py aby ustawić stany magazynowe i zdjęcia")

if __name__ == "__main__":
    main()