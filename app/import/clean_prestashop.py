#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do czyszczenia danych w PrestaShop
Usuwa wszystkie produkty, kategorie, producentów, cechy
"""

from tqdm import tqdm
from prestashop_api import get_api_xml, delete_api_resource, test_connection, PRESTASHOP_URL


def delete_all_products():
    """Usuwa wszystkie produkty"""
    print("\n" + "─"*60)
    print("► Usuwanie produktów...")
    
    xml = get_api_xml('products')
    if xml is None:
        print("❌ Nie udało się pobrać listy produktów")
        return 0
    
    products = xml.findall('.//product')
    total = len(products)
    
    if total == 0:
        print("  ✓ Brak produktów do usunięcia")
        return 0
    
    deleted = 0
    for product in tqdm(products, desc="  Produkty", ncols=80):
        product_id = product.get('id')
        if delete_api_resource('products', product_id):
            deleted += 1
    
    print(f"  ✓ Usunięto produktów: {deleted}/{total}")
    return deleted


def delete_all_manufacturers():
    """Usuwa wszystkich producentów"""
    print("\n" + "─"*60)
    print("► Usuwanie producentów...")
    
    xml = get_api_xml('manufacturers')
    if xml is None:
        print("❌ Nie udało się pobrać listy producentów")
        return 0
    
    manufacturers = xml.findall('.//manufacturer')
    total = len(manufacturers)
    
    if total == 0:
        print("  ✓ Brak producentów do usunięcia")
        return 0
    
    deleted = 0
    for manufacturer in tqdm(manufacturers, desc="  Producenci", ncols=80):
        manufacturer_id = manufacturer.get('id')
        if delete_api_resource('manufacturers', manufacturer_id):
            deleted += 1
    
    print(f"  ✓ Usunięto producentów: {deleted}/{total}")
    return deleted


def delete_custom_categories():
    """Usuwa wszystkie kategorie oprócz domyślnych (1=Root, 2=Home)"""
    print("\n" + "─"*60)
    print("► Usuwanie kategorii...")
    
    xml = get_api_xml('categories')
    if xml is None:
        print("❌ Nie udało się pobrać listy kategorii")
        return 0
    
    all_categories = xml.findall('.//category')
    categories = [c for c in all_categories if int(c.get('id')) > 2]
    total = len(categories)
    
    if total == 0:
        print("  ✓ Brak kategorii do usunięcia")
        return 0
    
    # Sortuj od najwyższych ID (usuń dzieci przed rodzicami)
    categories.sort(key=lambda c: int(c.get('id')), reverse=True)
    
    deleted = 0
    for category in tqdm(categories, desc="  Kategorie", ncols=80):
        category_id = category.get('id')
        if delete_api_resource('categories', category_id):
            deleted += 1
    
    print(f"  ✓ Usunięto kategorii: {deleted}/{total}")
    return deleted


def delete_all_features():
    """Usuwa wszystkie cechy produktów"""
    print("\n" + "─"*60)
    print("► Usuwanie cech produktów...")
    
    xml = get_api_xml('product_features')
    if xml is None:
        print("❌ Nie udało się pobrać listy cech")
        return 0
    
    features = xml.findall('.//product_feature')
    total = len(features)
    
    if total == 0:
        print("  ✓ Brak cech do usunięcia")
        return 0
    
    deleted = 0
    for feature in tqdm(features, desc="  Cechy", ncols=80):
        feature_id = feature.get('id')
        if delete_api_resource('product_features', feature_id):
            deleted += 1
    
    print(f"  ✓ Usunięto cech: {deleted}/{total}")
    return deleted


def main():
    """Główna funkcja"""
    print("\n" + "="*60)
    print("  CZYSZCZENIE BAZY DANYCH PRESTASHOP")
    print("="*60)
    
    # Sprawdź połączenie
    if not test_connection():
        print("\n❌ Nie można połączyć się z PrestaShop!")
        return 1
    
    print("\n✓ Połączenie z API: OK")
    print(f"✓ Adres: {PRESTASHOP_URL}")
    
    print("\n⚠️  Zostaną usunięte:")
    print("  • Wszystkie produkty")
    print("  • Wszyscy producenci")
    print("  • Wszystkie kategorie (oprócz Root i Home)")
    print("  • Wszystkie cechy produktów")
    
    
    delete_all_products()
    delete_all_manufacturers()
    delete_custom_categories()
    delete_all_features()
    
    print("\n" + "="*60)
    print("  ✓ CZYSZCZENIE ZAKOŃCZONE")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Przerwano przez użytkownika")
        exit(130)
