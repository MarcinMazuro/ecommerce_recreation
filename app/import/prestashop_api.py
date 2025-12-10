"""
Wspólny moduł z funkcjami API dla PrestaShop
"""

import requests
import xml.etree.ElementTree as ET
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

PRESTASHOP_URL = os.getenv('PRESTASHOP_URL', 'https://localhost:8443/api')
API_KEY = os.getenv('API_KEY')

if not API_KEY:
    raise ValueError("Brak API_KEY w pliku .env!")

session = requests.Session()
session.auth = (API_KEY, '')
session.verify = False

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_api_xml(endpoint, options=None):
    """
    Pobiera dane z API PrestaShop jako XML.
    
    Args:
        endpoint: Endpoint API (np. 'products', 'categories')
        options: Opcjonalne parametry zapytania
        
    Returns:
        ElementTree XML lub None w przypadku błędu
    """
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        response = session.get(url, params=options)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Błąd GET {url}: {e}", file=sys.stderr)
        return None


def post_api_xml(endpoint, xml_data):
    """
    Wysyła dane XML do API PrestaShop (POST).
    
    Args:
        endpoint: Endpoint API
        xml_data: Dane XML jako string
        
    Returns:
        ElementTree XML odpowiedzi lub None w przypadku błędu
    """
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        headers = {'Content-Type': 'application/xml'}
        response = session.post(url, data=xml_data.encode('utf-8'))
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            response_text = e.response.content.decode()
            if 'PHP Notice #8' in response_text and 'Trying to access array offset on value of type bool' in response_text:
                print(f"  Ignorowanie błędu PHP Notice #8", file=sys.stderr)
                try:
                    return ET.fromstring(e.response.content)
                except:
                    return None
        print(f"Błąd POST {url}: {e}\nOdpowiedź: {e.response.content.decode() if e.response else 'Brak odpowiedzi'}", file=sys.stderr)
        return None


def put_api_xml(endpoint, xml_data):
    """
    Aktualizuje dane w API PrestaShop (PUT).
    
    Args:
        endpoint: Endpoint API
        xml_data: Dane XML (string lub bytes)
        
    Returns:
        True jeśli sukces, False w przypadku błędu
    """
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}"
        response = session.put(url, data=xml_data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Błąd PUT {url}: {e}", file=sys.stderr)
        return False


def delete_api_resource(endpoint, resource_id):
    """
    Usuwa zasób z API PrestaShop (DELETE).
    
    Args:
        endpoint: Endpoint API
        resource_id: ID zasobu do usunięcia
        
    Returns:
        True jeśli sukces, False w przypadku błędu
    """
    try:
        url = f"{PRESTASHOP_URL}/{endpoint}/{resource_id}"
        response = session.delete(url)
        return response.status_code in [200, 204]
    except requests.exceptions.RequestException:
        return False


def has_product_images(product_id):
    """
    Sprawdza czy produkt ma już wgrane zdjęcia.

    Args:
        product_id: ID produktu

    Returns:
        True jeśli produkt ma zdjęcia, False w przeciwnym razie
    """
    try:
        url = f"{PRESTASHOP_URL}/images/products/{product_id}"
        response = session.get(url)

        if response.status_code == 200:
            # Parsuj XML aby sprawdzić czy są jakieś zdjęcia
            xml = ET.fromstring(response.content)
            images = xml.findall('.//image')
            return len(images) > 0
        return False
    except Exception:
        return False


def get_product_images_count(product_id):
    """
    Pobiera liczbę zdjęć jakie produkt ma w PrestaShop.

    Args:
        product_id: ID produktu

    Returns:
        Liczba zdjęć (int), 0 jeśli brak lub błąd
    """
    try:
        url = f"{PRESTASHOP_URL}/images/products/{product_id}"
        response = session.get(url)

        if response.status_code == 200:
            xml = ET.fromstring(response.content)
            images = xml.findall('.//image')
            return len(images)
        return 0
    except Exception:
        return 0


def post_image(product_id, image_path):
    """
    Wgrywa zdjęcie produktu do PrestaShop.
    
    Args:
        product_id: ID produktu
        image_path: Ścieżka do pliku zdjęcia
        
    Returns:
        True jeśli sukces, False w przypadku błędu
    """
    try:
        if not os.path.exists(image_path):
            print(f"  Błąd: Plik nie istnieje: {image_path}", file=sys.stderr)
            return False

        file_size = os.path.getsize(image_path)
        if file_size == 0:
            print(f"  Błąd: Plik jest pusty: {image_path}", file=sys.stderr)
            return False

        url = f"{PRESTASHOP_URL}/images/products/{product_id}"

        with open(image_path, 'rb') as img_file:
            files = {'image': ('product.jpg', img_file, 'image/jpeg')}
            response = session.post(url, files=files)

            if response.status_code != 200:
                print(f"  Błąd HTTP {response.status_code}: {response.text[:500]}", file=sys.stderr)

            response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"  Błąd wgrywania obrazu: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Odpowiedź serwera: {e.response.text[:500]}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  Nieoczekiwany błąd: {e}", file=sys.stderr)
        return False


def test_connection():
    """
    Testuje połączenie z API PrestaShop.
    
    Returns:
        True jeśli połączenie działa, False w przeciwnym razie
    """
    try:
        response = session.get(f"{PRESTASHOP_URL}/")
        return response.status_code == 200
    except:
        return False
