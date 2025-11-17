#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do czyszczenia danych w PrestaShop
Usuwa produkty, kategorie, producentów
"""

import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import sys

# --- KONFIGURACJA ---
PRESTASHOP_URL = 'https://localhost:8443/api'
API_KEY = '9HI4BPPVSZCVULACXFQUYMABJUE74X5V'

session = requests.Session()
session.auth = (API_KEY, '')
session.verify = False

# Wyłącz ostrzeżenia SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_api_xml(endpoint, options=None):
    """Pobiera dane z API jako XML"""
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        response = session.get(url, params=options)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Błąd GET {url}: {e}", file=sys.stderr)
        return None


def delete_resource(endpoint, resource_id):
    """Usuwa zasób po ID"""
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}/{resource_id}"
        response = session.delete(url)
        return response.status_code in [200, 204]
    except requests.exceptions.RequestException:
        return False


def delete_all_products():
    """Usuwa wszystkie produkty"""
    print("\n" + "="*60)
    print("USUWANIE PRODUKTÓW")
    print("="*60)
    
    xml = get_api_xml('products')
    if xml is None:
        print("❌ Nie udało się pobrać listy produktów")
        return 0
    
    products = xml.findall('.//product')
    total = len(products)
    
    if total == 0:
        print("ℹ️  Brak produktów do usunięcia")
        return 0
    
    print(f"📊 Znaleziono produktów: {total}")
    print(f"⚠️  Czy na pewno usunąć wszystkie produkty? (yes/no): ", end='')
    
    if input().strip().lower() not in ['yes', 'y', 'tak', 't']:
        print("⏭️  Pominięto usuwanie produktów")
        return 0
    
    deleted = 0
    for product in tqdm(products, desc="Usuwanie produktów"):
        product_id = product.get('id')
        if delete_resource('products', product_id):
            deleted += 1
    
    print(f"✅ Usunięto produktów: {deleted}/{total}")
    return deleted


def delete_all_manufacturers():
    """Usuwa wszystkich producentów"""
    print("\n" + "="*60)
    print("USUWANIE PRODUCENTÓW")
    print("="*60)
    
    xml = get_api_xml('manufacturers')
    if xml is None:
        print("❌ Nie udało się pobrać listy producentów")
        return 0
    
    manufacturers = xml.findall('.//manufacturer')
    total = len(manufacturers)
    
    if total == 0:
        print("ℹ️  Brak producentów do usunięcia")
        return 0
    
    print(f"📊 Znaleziono producentów: {total}")
    print(f"⚠️  Czy na pewno usunąć wszystkich producentów? (yes/no): ", end='')
    
    if input().strip().lower() not in ['yes', 'y', 'tak', 't']:
        print("⏭️  Pominięto usuwanie producentów")
        return 0
    
    deleted = 0
    for manufacturer in tqdm(manufacturers, desc="Usuwanie producentów"):
        manufacturer_id = manufacturer.get('id')
        if delete_resource('manufacturers', manufacturer_id):
            deleted += 1
    
    print(f"✅ Usunięto producentów: {deleted}/{total}")
    return deleted


def delete_custom_categories():
    """Usuwa wszystkie kategorie oprócz domyślnych (1=Root, 2=Home)"""
    print("\n" + "="*60)
    print("USUWANIE KATEGORII")
    print("="*60)
    
    xml = get_api_xml('categories')
    if xml is None:
        print("❌ Nie udało się pobrać listy kategorii")
        return 0
    
    all_categories = xml.findall('.//category')
    # Filtruj kategorie (pomiń 1=Root, 2=Home)
    categories = [c for c in all_categories if int(c.get('id')) > 2]
    total = len(categories)
    
    if total == 0:
        print("ℹ️  Brak kategorii do usunięcia (oprócz Root i Home)")
        return 0
    
    print(f"📊 Znaleziono kategorii niestandardowych: {total}")
    print(f"⚠️  Czy na pewno usunąć wszystkie kategorie? (yes/no): ", end='')
    
    if input().strip().lower() not in ['yes', 'y', 'tak', 't']:
        print("⏭️  Pominięto usuwanie kategorii")
        return 0
    
    # Sortuj od najniższych ID w dół (usuń dzieci przed rodzicami)
    categories.sort(key=lambda c: int(c.get('id')), reverse=True)
    
    deleted = 0
    for category in tqdm(categories, desc="Usuwanie kategorii"):
        category_id = category.get('id')
        if delete_resource('categories', category_id):
            deleted += 1
    
    print(f"✅ Usunięto kategorii: {deleted}/{total}")
    return deleted


def delete_all_images():
    """Usuwa wszystkie zdjęcia produktów"""
    print("\n" + "="*60)
    print("USUWANIE ZDJĘĆ")
    print("="*60)
    print("ℹ️  Zdjęcia zostaną usunięte automatycznie wraz z produktami")
    print("    (PrestaShop usuwa zdjęcia przy usuwaniu produktu)")
    return 0


def show_stats():
    """Wyświetla statystyki bazy danych"""
    print("\n" + "="*60)
    print("STATYSTYKI BAZY DANYCH")
    print("="*60)
    
    # Produkty
    xml = get_api_xml('products')
    products_count = len(xml.findall('.//product')) if xml else 0
    
    # Producenci
    xml = get_api_xml('manufacturers')
    manufacturers_count = len(xml.findall('.//manufacturer')) if xml else 0
    
    # Kategorie (bez Root i Home)
    xml = get_api_xml('categories')
    if xml:
        all_cats = xml.findall('.//category')
        categories_count = len([c for c in all_cats if int(c.get('id')) > 2])
    else:
        categories_count = 0
    
    print(f"\n📊 Aktualne dane:")
    print(f"  • Produkty: {products_count}")
    print(f"  • Producenci: {manufacturers_count}")
    print(f"  • Kategorie (niestandardowe): {categories_count}")
    print()


def main():
    """Główna funkcja"""
    print("="*60)
    print("  CZYSZCZENIE DANYCH PRESTASHOP")
    print("="*60)
    print(f"\n📍 Sklep: {PRESTASHOP_URL}")
    print()
    
    # Sprawdź połączenie
    try:
        response = session.get(f"{PRESTASHOP_URL}/")
        if response.status_code != 200:
            print("❌ Brak połączenia z API PrestaShop!")
            return 1
    except:
        print("❌ Nie można połączyć się z PrestaShop!")
        return 1
    
    print("✅ Połączenie OK\n")
    
    # Pokaż statystyki
    show_stats()
    
    # Menu
    while True:
        print("="*60)
        print("OPCJE CZYSZCZENIA")
        print("="*60)
        print("1. Usuń wszystkie produkty")
        print("2. Usuń wszystkich producentów")
        print("3. Usuń wszystkie kategorie (oprócz Root i Home)")
        print("4. Usuń WSZYSTKO (produkty + producenci + kategorie)")
        print("5. Pokaż statystyki")
        print("0. Wyjście")
        print()
        
        choice = input("Wybierz opcję (0-5): ").strip()
        
        if choice == '1':
            delete_all_products()
            show_stats()
        elif choice == '2':
            delete_all_manufacturers()
            show_stats()
        elif choice == '3':
            delete_custom_categories()
            show_stats()
        elif choice == '4':
            print("\n⚠️  ⚠️  ⚠️  UWAGA! ⚠️  ⚠️  ⚠️")
            print("To usunie WSZYSTKIE dane:")
            print("  • Wszystkie produkty")
            print("  • Wszystkich producentów")
            print("  • Wszystkie kategorie (oprócz Root i Home)")
            print("\nTej operacji NIE MOŻNA cofnąć!")
            print(f"\nWpisz 'DELETE ALL' aby potwierdzić: ", end='')
            
            if input().strip() == 'DELETE ALL':
                print("\n🗑️  Rozpoczynam czyszczenie...")
                delete_all_products()
                delete_all_manufacturers()
                delete_custom_categories()
                print("\n✅ Czyszczenie zakończone!")
                show_stats()
            else:
                print("❌ Anulowano")
        elif choice == '5':
            show_stats()
        elif choice == '0':
            print("\n👋 Do widzenia!")
            break
        else:
            print("❌ Nieprawidłowa opcja\n")
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Przerwano przez użytkownika")
        exit(130)
