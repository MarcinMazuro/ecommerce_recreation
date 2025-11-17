#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Główny skrypt zarządzający importem danych do PrestaShop.

Automatycznie wykonuje:
1. Import kategorii
2. Import produktów
3. Aktualizacja stocków i zdjęć
4. Podsumowanie statystyk
"""

import sys
import subprocess
import time
from pathlib import Path

class ImportManager:
    """Zarządza procesem importu danych do PrestaShop."""
    
    def __init__(self):
        self.stats = {
            'start_time': None,
            'end_time': None,
            'categories_imported': False,
            'products_imported': False,
            'stocks_updated': False,
            'images_uploaded': False,
            'errors': []
        }
        self.base_dir = Path(__file__).parent
    
    def print_header(self, title):
        """Wyświetla nagłówek sekcji."""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")
    
    def print_menu(self):
        """Wyświetla główne menu."""
        print("""

Dostępne opcje:

  [1] Pełny import
  [0] Wyjście

""")
    
    def run_script(self, script_name, description):
        """Uruchamia skrypt pythonowy."""
        print(f"\n{'─'*70}")
        print(f"► {description}")
        print(f"{'─'*70}\n")
        
        script_path = self.base_dir / script_name
        
        if not script_path.exists():
            error_msg = f"Błąd: Nie znaleziono skryptu {script_name}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
        
        try:
            # Uruchom skrypt w tym samym interpreterze Python
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.base_dir.parent / 'data'),
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print(f"\n✓ {description} - ZAKOŃCZONO POMYŚLNIE")
                return True
            else:
                error_msg = f"{description} - BŁĄD (kod: {result.returncode})"
                print(f"\n✗ {error_msg}")
                self.stats['errors'].append(error_msg)
                return False
                
        except KeyboardInterrupt:
            print(f"\n\n⚠️  Przerwano przez użytkownika")
            return False
        except Exception as e:
            error_msg = f"{description} - WYJĄTEK: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False

    
    def clean_database(self):
        """Czyści bazę danych PrestaShop."""
        self.print_header("CZYSZCZENIE BAZY DANYCH")
        
        print("⚠️  UWAGA: Ta operacja usunie:")
        print("  • Wszystkie produkty")
        print("  • Wszystkie kategorie (oprócz domyślnych)")
        print("  • Wszystkie producerów")
        print("  • Wszystkie cechy produktów")
        print()
        
        return self.run_script('clean_prestashop.py', 'Czyszczenie bazy danych')
    
    def import_categories(self):
        """Importuje kategorie."""
        self.print_header("IMPORT KATEGORII")
        success = self.run_script('import_categories.py', 'Import kategorii')
        if success:
            self.stats['categories_imported'] = True
        return success
    
    def import_products(self):
        """Importuje produkty."""
        self.print_header("IMPORT PRODUKTÓW")
        success = self.run_script('import_products.py', 'Import produktów')
        if success:
            self.stats['products_imported'] = True
        return success
    
    def update_stocks_images(self):
        """Aktualizuje stany magazynowe i zdjęcia."""
        self.print_header("AKTUALIZACJA STOCKÓW I ZDJĘĆ")
        success = self.run_script('update_stocks_images.py', 'Aktualizacja stocków i zdjęć')
        if success:
            self.stats['stocks_updated'] = True
            self.stats['images_uploaded'] = True
        return success
    
    def full_import(self):
        """Przeprowadza pełny proces importu."""
        self.print_header("PEŁNY IMPORT DANYCH")
        
        print("Zostanie wykonana następująca sekwencja:")
        print("  1. Czyszczenie bazy danych (opcjonalne)")
        print("  2. Import kategorii")
        print("  3. Import produktów")
        print("  4. Aktualizacja stocków i zdjęć")
        print()
        
        self.stats['start_time'] = time.time()
        
        # Krok 1: Czyszczenie (opcjonalne)
        self.clean_database()
        # Krok 2: Kategorie
        self.import_categories()
        print("\n\n")
        self.import_products()
        # Krok 4: Stocki i zdjęcia
        print("\n\n")
        self.update_stocks_images()
        
        self.stats['end_time'] = time.time()
        
        # Podsumowanie
        print("\n\n")
        self.show_summary()
    
    def show_summary(self):
        """Wyświetla podsumowanie importu."""
        self.print_header("PODSUMOWANIE IMPORTU")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            print(f"⏱️  Czas trwania: {minutes}m {seconds}s\n")
        
        print("Status wykonanych operacji:\n")
        
        statuses = [
            ("Kategorie", self.stats['categories_imported']),
            ("Produkty", self.stats['products_imported']),
            ("Stany magazynowe", self.stats['stocks_updated']),
            ("Zdjęcia", self.stats['images_uploaded'])
        ]
        
        for name, status in statuses:
            icon = "✓" if status else "✗"
            status_text = "Zaimportowane" if status else "Nie wykonane"
            print(f"  {icon} {name:.<30} {status_text}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Wystąpiło błędów: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  • {error}")
        else:
            print("\n✓ Import zakończony bez błędów")
        
        print()
    
    def wait_for_user(self):
        """Czeka na naciśnięcie klawisza przez użytkownika."""
        input("\nNaciśnij ENTER aby kontynuować...")
    
    def run(self):
        """Uruchamia główną pętlę menu."""
        while True:
            self.print_menu()
            
            try:
                choice = input("Wybierz opcję [0-6]: ").strip()
                
                if choice == '0':
                    print("\n👋 Do widzenia!\n")
                    break
                    
                elif choice == '1':
                    self.full_import()
                    self.wait_for_user()
                    
                else:
                    print("\n❌ Nieprawidłowa opcja. Wybierz liczbę od 0 do 6.")
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print("\n\n👋 Przerwano. Do widzenia!\n")
                break
            except Exception as e:
                print(f"\n❌ Błąd: {e}")
                self.wait_for_user()


def main():
    """Główna funkcja."""
    manager = ImportManager()
    manager.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
