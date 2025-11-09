import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import time
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def collect_all_categories(categories, parent_name=''):
    """Rekursywnie zbiera tylko kategorie końcowe (bez podkategorii)"""
    all_cats = []

    for category in categories:
        cat_name = category.get('name', '')
        cat_url = category.get('url', '')
        subcategories = category.get('subcategories', [])

        if not cat_url or cat_url == '#':
            if subcategories:
                full_name = f"{parent_name}/{cat_name}" if parent_name else cat_name
                all_cats.extend(collect_all_categories(subcategories, full_name))
            continue

        full_name = f"{parent_name}/{cat_name}" if parent_name else cat_name

        if cat_url.startswith('/'):
            cat_url = f"https://dobreziele.pl{cat_url}"

        if len(subcategories) == 0:
            all_cats.append({
                'name': cat_name,
                'full_path': full_name,
                'url': cat_url
            })
        else:
            all_cats.extend(collect_all_categories(subcategories, full_name))

    return all_cats


def scrape_products_from_category(category_url):
    """Scrapuje produkty z danej kategorii"""
    products = []

    try:
        response = requests.get(category_url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Znajdź wszystkie produkty - są w div class="shop-item"
        product_items = soup.find_all('div', class_='shop-item')

        print(f"Znaleziono {len(product_items)} produktów na stronie")

        for item in product_items:
            try:
                product_data = {}

                # Główny link produktu - drugi link <a> który zawiera nazwę, opis i cenę
                main_link = item.find('a', href=True, title=False)
                if main_link:
                    product_data['url_produktu'] = main_link.get('href')

                    # Nazwa produktu - pierwszy tekst w linku (jeśli nie mamy z title)
                    if 'nazwa' not in product_data:
                        # Pobierz bezpośrednią zawartość tekstową (bez potomków)
                        for content in main_link.contents:
                            if isinstance(content, str) and content.strip():
                                product_data['nazwa'] = content.strip()
                                break

                # ID produktu - z formularza dodawania do koszyka
                form = item.find('form')
                if form:
                    id_input = form.find('input', {'name': 'id'})
                    if id_input:
                        product_data['id_produktu'] = id_input.get('value')

                # Dodaj produkt do listy tylko jeśli ma nazwę
                if product_data.get('nazwa'):
                    products.append(product_data)

            except Exception as e:
                print(f"Błąd podczas parsowania produktu: {e}")
                continue

    except requests.RequestException as e:
        print(f"Błąd podczas pobierania {category_url}: {e}")

    return products


if __name__ == '__main__':
    # Wczytaj kategorie i scrapuj produkty
    categories_path = Path(__file__).resolve().parent.parent / 'data' / 'categories.json'

    if not categories_path.exists():
        print(f"Nie znaleziono pliku {categories_path}")
        exit(1)

    with open(categories_path, 'r', encoding='utf-8') as f:
        categories_data = json.load(f)

    # Zbierz wszystkie kategorie i podkategorie
    all_categories = collect_all_categories(categories_data)

    print(f"\n{'='*60}")
    print(f"Znaleziono {len(all_categories)} kategorii do zescrapowania")
    print(f"{'='*60}\n")

    all_products = []
    for i, category in enumerate(all_categories, 1):
        print(f"\n[{i}/{len(all_categories)}] {'='*60}")
        print(f"Kategoria: {category['full_path']}")
        print(f"URL: {category['url']}")
        print(f"{'='*60}")

        products = scrape_products_from_category(category['url'])

        # Dodaj informację o kategorii do każdego produktu
        for product in products:
            product['kategoria'] = category['name']
            product['kategoria_pelna_sciezka'] = category['full_path']
            product['url_kategorii'] = category['url']

        all_products.extend(products)
        print(f"Zescrapowano {len(products)} produktów z tej kategorii")

        # Opóźnienie między kategoriami
        time.sleep(1)

    # Zapisz wszystkie produkty do pliku JSON
    output_path = Path(__file__).resolve().parent.parent / 'data' / 'products.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_products, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"✓ ZAKOŃCZONO SCRAPOWANIE")
    print(f"✓ Łącznie zescrapowano {len(all_products)} produktów")
    print(f"✓ Dane zapisano do: {output_path}")
    print(f"{'='*60}")

    # Pokaż przykładowe produkty
    if all_products:
        print("\nPrzykładowy produkt:")
        print(json.dumps(all_products[0], indent=2, ensure_ascii=False))
