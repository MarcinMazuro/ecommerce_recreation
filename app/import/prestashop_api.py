"""
Wspólny moduł z funkcjami API dla PrestaShop
"""

import requests
import xml.etree.ElementTree as ET
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe z .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Konfiguracja z .env
PRESTASHOP_URL = os.getenv('PRESTASHOP_URL', 'https://localhost:8443/api')
API_KEY = os.getenv('API_KEY')

if not API_KEY:
    raise ValueError("Brak API_KEY w pliku .env!")

# Sesja globalna
session = requests.Session()
session.auth = (API_KEY, '')
session.verify = False

# Wyłącz ostrzeżenia SSL
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
        # Sprawdź czy to ignorowalny błąd PHP Notice #8
        if e.response is not None:
            response_text = e.response.content.decode()
            if 'PHP Notice #8' in response_text and 'Trying to access array offset on value of type bool' in response_text:
                print(f"  Ignorowanie błędu PHP Notice #8 (znany problem PrestaShop)", file=sys.stderr)
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
        url = f"{PRESTASHOP_URL}/images/products/{product_id}"
        with open(image_path, 'rb') as img_file:
            files = {'image': (os.path.basename(image_path), img_file, 'image/jpeg')}
            response = session.post(url, files=files)
            response.raise_for_status()
        return True
    except Exception as e:
        print(f"  Błąd wgrywania obrazu: {e}", file=sys.stderr)
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
