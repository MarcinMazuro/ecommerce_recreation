import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from typing import Dict


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def scrape_product_details(product_url: str) -> Dict:
    """
    Scrapuje szczegółowe informacje o produkcie ze strony produktu.

    Args:
        product_url: URL strony produktu

    Returns:
        Słownik z danymi produktu zawierający:
        - nazwa: nazwa produktu
        - cena: cena produktu
        - opis: szczegółowy opis produktu
        - marka: marka produktu
        - kategoria: kategoria produktu (breadcrumbs)
        - zdjecia: lista URL zdjęć w wysokiej rozdzielczości
        - szczegoly: dodatkowe szczegóły (skład, kraj pochodzenia, etc.)
    """
    try:
        response = requests.get(product_url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        product_data = {
            'url': product_url,
            'nazwa': None,
            'cena': None,
            'opis': None,
            'marka': None,
            'kategoria': None,
            'zdjecia': [],
            'szczegoly': {}
        }

        h1_tag = soup.find('h1')
        if h1_tag:
            product_data['nazwa'] = h1_tag.get_text(strip=True)

        price_div = soup.find('div', class_='promoprice')
        if price_div:
            product_data['cena'] = price_div.get_text(strip=True)

        breadcrumbs = soup.find('h3', class_='breadcrumbs')
        if breadcrumbs:
            links = breadcrumbs.find_all('a')
            if links:
                categories = [link.get_text(strip=True) for link in links]
                product_data['kategoria'] = ' > '.join(categories)

        marka_text = soup.find(string=re.compile(r'Marka:'))
        if marka_text:
            parent = marka_text.parent
            if parent:
                strong_tag = parent.find('strong')
                if strong_tag:
                    marka_link = strong_tag.find('a')
                    if marka_link:
                        product_data['marka'] = marka_link.get_text(strip=True)

        # Pobierz wszystkie zdjęcia z klasy fancybox
        fancybox_links = soup.find_all('a', class_='fancybox')
        for fancybox_link in fancybox_links:
            if fancybox_link and fancybox_link.get('href'):
                image_url = fancybox_link.get('href')
                if image_url and image_url not in product_data['zdjecia']:
                    product_data['zdjecia'].append(image_url)

        picture_div = soup.find('div', class_='picture')
        if picture_div:
            img_links = picture_div.find_all('a', href=re.compile(r'\.jpg|\.png|\.jpeg', re.IGNORECASE))
            for link in img_links:
                img_url = link.get('href')
                if img_url and img_url not in product_data['zdjecia']:
                    if '/b_' in img_url or img_url.endswith('.jpg') or img_url.endswith('.png'):
                        product_data['zdjecia'].append(img_url)



        moredesc_div = soup.find('div', class_='moredesc')
        if moredesc_div:
            description_text = moredesc_div.get_text(separator='\n', strip=True)
            product_data['opis'] = description_text

        details_table = soup.find('table')
        if details_table:
            rows = details_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True).replace(':', '')
                    value = cells[1].get_text(separator=' ', strip=True)
                    product_data['szczegoly'][key] = value

        return product_data

    except Exception as e:
        print(f"Błąd podczas scrapowania {product_url}: {e}")
        return None


def scrape_all_products(products_file: str, output_file: str, delay: float = 1.0):
    """
    Scrapuje szczegóły wszystkich produktów z pliku products.json

    Args:
        products_file: Ścieżka do pliku JSON z listą produktów
        output_file: Ścieżka do pliku wyjściowego z szczegółami produktów
        delay: Opóźnienie między requestami w sekundach (domyślnie 1.0)
        max_products: Maksymalna liczba produktów do przetworzenia (None = wszystkie)

    Returns:
        Lista produktów z szczegółami
    """
    import time

    try:
        with open(products_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        print(f"Błąd podczas wczytywania pliku {products_file}: {e}")
        return []

    print(f"Znaleziono {len(products)} wpisów w pliku products.json")

    unique_products = {}
    for product in products:
        url = product.get('url_produktu')
        if url and url not in unique_products:
            unique_products[url] = product

    products = list(unique_products.values())
    print(f"Po deduplikacji: {len(products)} unikalnych produktów")

    enriched_products = []
    failed_products = []

    start_time = time.time()

    for i, product in enumerate(products, 1):
        product_url = product.get('url_produktu')
        if not product_url:
            print(f"[{i}/{len(products)}] Brak URL dla produktu, pomijam")
            failed_products.append({
                'product': product,
                'error': 'Brak URL'
            })
            continue

        if i % 50 == 0 or i == 1:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(products) - i) / rate if rate > 0 else 0
            print(f"\n[{i}/{len(products)}] Postęp: {i/len(products)*100:.1f}% | "
                  f"Tempo: {rate:.2f} prod/s | Pozostało: ~{remaining/60:.0f} min\n")

        print(f"[{i}/{len(products)}] Scrapuję: {product.get('nazwa', 'Unknown')}...")

        try:
            details = scrape_product_details(product_url)

            if details and details.get('nazwa'):
                enriched_product = {
                    **product,
                    'szczegoly_produktu': details
                }
                enriched_products.append(enriched_product)
                print(f"    ✓ Pobrano szczegóły ({len(details.get('zdjecia', []))} zdjęć)")
            else:
                print(f"    ✗ Nie udało się pobrać szczegółów")
                failed_products.append({
                    'product': product,
                    'error': 'Brak danych ze strony'
                })

            if i < len(products):
                time.sleep(delay)

        except Exception as e:
            print(f"    ✗ Błąd: {e}")
            failed_products.append({
                'product': product,
                'error': str(e)
            })

    print(f"\n=== Podsumowanie ===")
    print(f"Pomyślnie przetworzono: {len(enriched_products)}/{len(products)} produktów")
    print(f"Niepowodzenia: {len(failed_products)}")

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_products, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Dane zapisane do: {output_file}")
    except Exception as e:
        print(f"✗ Błąd podczas zapisywania: {e}")



def main():
    """Główna funkcja - pobiera szczegóły wszystkich produktów"""

    import sys

    script_dir = Path(__file__).parent
    products_file = script_dir.parent / "data" / "products.json"
    output_file = script_dir.parent / "data" / "products_with_details.json"

    if not products_file.exists():
        print(f"Błąd: Nie znaleziono pliku {products_file}")
        print("Najpierw uruchom product_scraper.py aby pobrać listę produktów")
        return

    scrape_all_products(
        products_file=str(products_file),
        output_file=str(output_file),
        delay=1.0,  # 1.0 sekundy między requestami
    )




if __name__ == "__main__":
    main()

