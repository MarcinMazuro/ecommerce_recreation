#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania zdjęć produktów w wysokiej rozdzielczości.

Zgodny z wymaganiami:
- Pobiera jedno zdjęcie produktu w wysokiej rozdzielczości
- Zapisuje zdjęcia umożliwiające powiększenie (nie miniatury)
- Organizuje obrazy według kategorii i produktów
"""

import json
import os
import requests
from pathlib import Path
from urllib.parse import urlparse
import time
from typing import Dict, List, Optional
import re


class ImageDownloader:
    """Klasa do pobierania i zarządzania zdjęciami produktów."""
    
    def __init__(self, output_dir: str = "app/data/images"):
        """
        Inicjalizacja downloadera.
        
        Args:
            output_dir: Katalog główny dla pobranych obrazów
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statystyki
        self.stats = {
            'total_products': 0,
            'downloaded_images': 0,
            'failed_downloads': 0,
            'skipped_existing': 0
        }
        
        # Headers do requestów
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': 'https://dobreziele.pl/'
        }
    
    def sanitize_filename(self, name: str) -> str:
        """Oczyszcza nazwę pliku z niedozwolonych znaków."""
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)
        return name[:100]
    
    def get_high_res_url(self, url: str) -> List[str]:
        """
        Generuje liste URL-i od najwyzszej do najnizszej rozdzielczosci.
        
        Dla dobreziele.pl:
        - o_shop_ID.jpg - oryginal (najwyzsza rozdzielczosc)
        - shop_ID.jpg - srednia rozdzielczosc
        - b_shop_ID.jpg - miniatura (unikamy)
        """
        base_url = url.split('?')[0]
        variants = []
        
        if 'b_shop_' in base_url:
            # Oryginał
            variants.append(base_url.replace('b_shop_', 'o_shop_'))
            # Średni rozmiar
            variants.append(base_url.replace('b_shop_', 'shop_'))
            # Miniatura jako ostatnia opcja
            variants.append(base_url)
        else:
            variants.append(base_url)
        
        return variants
    
    def download_image(self, url: str, output_path: Path, min_size_kb: int = 15) -> bool:
        """
        Pobiera obraz z URL.
        
        Args:
            url: URL obrazu
            output_path: Ścieżka zapisu
            min_size_kb: Minimalny rozmiar w KB
            
        Returns:
            True jeśli sukces
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30, stream=True)
            
            if response.status_code == 200:
                content_length = int(response.headers.get('content-length', 0))
                
                if content_length < min_size_kb * 1024:
                    return False
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = output_path.stat().st_size
                if file_size < min_size_kb * 1024:
                    output_path.unlink()
                    return False
                
                print(f"✓ {output_path.name} ({file_size / 1024:.1f} KB)")
                return True
            
            return False
                
        except Exception as e:
            print(f"✗ Błąd: {e}")
            return False
    
    def download_product_image(self, product: Dict, force: bool = False) -> bool:
        """
        Pobiera zdjęcie produktu w najwyższej dostępnej rozdzielczości.
        
        Args:
            product: Dane produktu
            force: Czy nadpisać istniejące
            
        Returns:
            True jeśli pobrano
        """
        product_id = product.get('id_produktu', 'unknown')
        product_name = product.get('nazwa', 'unknown')
        
        # Prosta struktura: images/id_nazwa/
        safe_name = self.sanitize_filename(product_name)
        
        product_dir = self.output_dir / f"{product_id}_{safe_name}"
        product_dir.mkdir(parents=True, exist_ok=True)
        
        # URL zdjęcia
        image_urls = []
        if 'szczegoly_produktu' in product and 'zdjecia' in product['szczegoly_produktu']:
            image_urls = product['szczegoly_produktu']['zdjecia']
        
        if not image_urls:
            print(f"⚠️  Brak zdjęć: {product_name}")
            return False
        
        # Pobierz pierwsze zdjęcie
        img_url = image_urls[0]
        variants = self.get_high_res_url(img_url)
        
        ext = Path(urlparse(img_url).path).suffix or '.jpg'
        output_path = product_dir / f"product{ext}"
        
        # Sprawdź czy istnieje
        if output_path.exists() and not force:
            file_size = output_path.stat().st_size
            print(f"⊙ Już istnieje ({file_size / 1024:.1f} KB)")
            self.stats['skipped_existing'] += 1
            return True
        
        # Próbuj pobrać od najwyższej rozdzielczości
        for variant_url in variants:
            if self.download_image(variant_url, output_path):
                self.stats['downloaded_images'] += 1
                return True
        
        print(f"✗ Nie udało się pobrać")
        self.stats['failed_downloads'] += 1
        return False
    
    def process_products_file(self, json_file: str, max_products: Optional[int] = None,
                             force: bool = False):
        """
        Przetwarza plik JSON i pobiera zdjęcia.
        
        Args:
            json_file: Plik JSON z produktami
            max_products: Limit produktów (None = wszystkie)
            force: Czy nadpisać istniejące
        """
        print(f"\n{'='*70}")
        print(f"📥 POBIERANIE ZDJĘĆ PRODUKTÓW")
        print(f"{'='*70}\n")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        if max_products:
            products = products[:max_products]
        
        self.stats['total_products'] = len(products)
        
        print(f"📊 Produktów: {len(products)}")
        print(f"📁 Katalog: {self.output_dir.absolute()}\n")
        
        for idx, product in enumerate(products, start=1):
            product_name = product.get('nazwa', 'unknown')
            product_id = product.get('id_produktu', 'unknown')
            
            print(f"[{idx}/{len(products)}] {product_name} (ID: {product_id})")
            self.download_product_image(product, force)
            
            time.sleep(0.1)  # Przerwa między requestami
            
            if idx % 20 == 0:
                self.print_stats(True)
        
        print(f"\n{'='*70}")
        print(f"✓ ZAKOŃCZONO")
        print(f"{'='*70}\n")
        self.print_stats()
    
    def print_stats(self, interim: bool = False):
        """Wyświetla statystyki."""
        prefix = "📊 Statystyki częściowe" if interim else "📊 Statystyki końcowe"
        
        print(f"\n{prefix}:")
        print(f"  • Produktów: {self.stats['total_products']}")
        print(f"  • Pobrano: {self.stats['downloaded_images']}")
        print(f"  • Pominięto: {self.stats['skipped_existing']}")
        print(f"  • Błędów: {self.stats['failed_downloads']}\n")


def main():
    """Główna funkcja."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pobieranie zdjęć produktów w wysokiej rozdzielczości',
        epilog="""
Przykłady:
  # Test - pierwsze 10 produktów
  python image_downloader.py --max-products 10
  
  # Wszystkie produkty
  python image_downloader.py
  
  # Nadpisz istniejące
  python image_downloader.py --force
        """
    )
    
    parser.add_argument('--input', default='app/data/products_with_details.json',
                       help='Plik JSON z produktami')
    parser.add_argument('--output', default='app/data/images',
                       help='Katalog dla zdjęć')
    parser.add_argument('--max-products', type=int,
                       help='Maksymalna liczba produktów')
    parser.add_argument('--force', action='store_true',
                       help='Nadpisz istniejące pliki')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f" Błąd: Plik {args.input} nie istnieje!")
        return 1
    
    downloader = ImageDownloader(output_dir=args.output)
    
    try:
        downloader.process_products_file(args.input, args.max_products, args.force)
        return 0
    except KeyboardInterrupt:
        print("\n\n Przerwano")
        downloader.print_stats()
        return 130
    except Exception as e:
        print(f"\n Błąd: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
