import time
import random
import string
import os
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- KONFIGURACJA ---
BASE_URL = "https://localhost:8443/"  # Upewnij się, że URL jest poprawny
CATEGORY_URLS = [
    "https://localhost:8443/694-yerba-klasyczna",
    "https://localhost:8443/696-chimarrao"
]
SEARCH_TERM = "Algarrobo Tostado Cometa" # Upewnij się, że ten produkt istnieje

def generate_random_email():
    return ''.join(random.choices(string.ascii_lowercase, k=10)) + "@test.com"

# --- INICJALIZACJA ---
chrome_options = Options()
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-insecure-localhost')
# chrome_options.add_argument('--headless') # Odkomentuj, jeśli chcesz by działało w tle (szybciej)

# Ustawienia pobierania PDF (żeby nie otwierało w oknie, tylko pobierało)
prefs = {
    "download.default_directory": os.getcwd(),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.maximize_window()
# Skrócony ogólny timeout, żeby szybciej wykrywał braki elementów, ale wystarczający na ładowanie
wait = WebDriverWait(driver, 8) 

successful_urls = set()
failed_urls = set()

try:
    start_time = time.time()
    print("--- START TESTU ---")

    # 1. DODANIE 10 UNIKATOWYCH PRODUKTÓW
    print("1. Dodawanie 10 UNIKATOWYCH produktów (ilość 1-3)...")
    
    while len(successful_urls) < 10:
        # Round-robin po kategoriach zapewnia różnorodność
        for cat_url in CATEGORY_URLS:
            if len(successful_urls) >= 10: break
            
            driver.get(cat_url)
            
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature")))
                
                # Pobieranie linków
                try:
                    product_elements = driver.find_elements(By.CSS_SELECTOR, ".product-miniature a.thumbnail")
                    page_urls = [elem.get_attribute("href") for elem in product_elements]
                except StaleElementReferenceException:
                    page_urls = [] # Pomiń w tym obrocie, jeśli strona przeładowała
                
                # Wybieramy tylko te, których jeszcze nie mamy
                available_urls = [url for url in page_urls if url not in successful_urls and url not in failed_urls]
                
                if not available_urls:
                    continue
                
                target_url = random.choice(available_urls)
                driver.get(target_url)
                
                # --- PROCES DODAWANIA ---
                try:
                    add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".add-to-cart")))
                    
                    # Sprawdzenie dostępności
                    try:
                        unavailable_msg = driver.find_elements(By.ID, "product-availability")
                        if unavailable_msg and ("nie" in unavailable_msg[0].text.lower() or "out" in unavailable_msg[0].text.lower()):
                             raise TimeoutException 
                    except NoSuchElementException:
                        pass 

                    # --- ZMIANA ILOŚCI (Usprawniona) ---
                    target_qty = random.randint(1, 3)
                    
                    if target_qty > 1:
                        try:
                            qty_input = driver.find_element(By.ID, "quantity_wanted")
                            qty_input.click()
                            # Używamy Ctrl+A (lub Cmd+A) aby zaznaczyć wszystko i nadpisać
                            qty_input.send_keys(Keys.CONTROL + "a") 
                            qty_input.send_keys(Keys.DELETE)
                            qty_input.send_keys(str(target_qty))
                            # Kliknięcie w bok, aby wymusić walidację PrestaShop
                            driver.find_element(By.CSS_SELECTOR, "h1[itemprop='name']").click()
                            time.sleep(0.5) 
                        except Exception as e:
                            print(f"   ⚠️ Błąd zmiany ilości. Zostaje 1 szt.")

                    # JS click jest bezpieczniejszy dla przycisku Add to cart
                    driver.execute_script("arguments[0].click();", add_btn)
                    
                    # Obsługa modala
                    wait.until(EC.visibility_of_element_located((By.ID, "blockcart-modal")))
                    continue_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#blockcart-modal .btn.btn-secondary")))
                    driver.execute_script("arguments[0].click();", continue_btn)
                    
                    # SUKCES
                    successful_urls.add(target_url)
                    print(f"   ✅ [{len(successful_urls)}/10] Dodano: {target_url[-20:]}... (Ilość: {target_qty})")

                except TimeoutException:
                    # print("   ⚠️ Produkt niedostępny/timeout.")
                    failed_urls.add(target_url)
                    continue

            except TimeoutException:
                continue

    # 2. WYSZUKIWANIE
    print("2. Wyszukiwanie produktu...")
    driver.get(BASE_URL) 
    try:
        search_input = wait.until(EC.visibility_of_element_located((By.NAME, "s")))
        search_input.clear()
        search_input.send_keys(SEARCH_TERM)
        search_input.send_keys(Keys.RETURN)
        
        search_results = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature")))
        
        if search_results:
            print(f"   Znaleziono {len(search_results)} wyników. Wybieram losowy.")
            random_res = random.choice(search_results)
            res_link = random_res.find_element(By.TAG_NAME, "a")
            # Pobieramy href i idziemy tam bezpośrednio (stabilniejsze niż click w liście wyników)
            driver.get(res_link.get_attribute("href"))

            add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".add-to-cart")))
            driver.execute_script("arguments[0].click();", add_btn)
            
            wait.until(EC.visibility_of_element_located((By.ID, "blockcart-modal")))
            cont_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#blockcart-modal .btn.btn-secondary")))
            driver.execute_script("arguments[0].click();", cont_btn)
            print("   ✅ Produkt z wyszukiwania dodany.")
    except TimeoutException:
        print(f"   ⚠️ Błąd wyszukiwania '{SEARCH_TERM}'.")

    # 3. USUNIĘCIE 3 PRODUKTÓW Z KOSZYKA
    print("3. Usuwanie produktów z koszyka...")
    driver.get(BASE_URL + "/index.php?controller=cart&action=show")
    
    for i in range(3):
        try:
            # Czekamy na listę, żeby upewnić się że koszyk się załadował
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cart-items")))
            delete_buttons = driver.find_elements(By.CSS_SELECTOR, ".remove-from-cart")
            
            if not delete_buttons:
                break
                
            # Zapamiętujemy element, który ma zniknąć (dla wait.staleness)
            item_container = delete_buttons[0].find_element(By.XPATH, "./ancestor::li") 
            
            driver.execute_script("arguments[0].click();", delete_buttons[0])
            
            # Czekamy aż ten konkretny element zniknie z DOM (zamiast time.sleep)
            wait.until(EC.staleness_of(item_container))
            print(f"   🗑️ Usunięto produkt {i+1}")
            
        except Exception as e:
            print(f"   Koniec usuwania lub błąd: {e}")
            break

    # 4. REJESTRACJA
    print("4. Rejestracja...")
    driver.get(BASE_URL + "/index.php?controller=order")
    
    try:
        driver.find_element(By.ID, "field-id_gender-1").click()
        driver.find_element(By.ID, "field-firstname").send_keys("Jan")
        driver.find_element(By.ID, "field-lastname").send_keys("Automatyczny")
        driver.find_element(By.ID, "field-email").send_keys(generate_random_email())
        driver.find_element(By.ID, "field-password").send_keys("Haslo1234!")
        driver.find_element(By.ID, "field-birthday").send_keys("1990-01-01")
        
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "form#customer-form input[type='checkbox']")
        for cb in checkboxes:
            driver.execute_script("arguments[0].click();", cb)

        driver.find_element(By.CSS_SELECTOR, "button[data-link-action='register-new-customer']").click()
        print("   ✅ Zarejestrowano.")
    except Exception as e:
        print(f"   ⚠️ Błąd rejestracji (może już zalogowany?): {e}")

    # 5. ADRES
    print("5. Adres...")
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "field-address1"))).send_keys("Ulica Testowa 123")
        driver.find_element(By.ID, "field-postcode").send_keys("00-001")
        driver.find_element(By.ID, "field-city").send_keys("Warszawa")
        
        confirm_addr_btn = driver.find_element(By.NAME, "confirm-addresses")
        driver.execute_script("arguments[0].click();", confirm_addr_btn)
        print("   ✅ Adres dodany.")
    except TimeoutException:
        print("   ℹ️ Adres prawdopodobnie już uzupełniony.")

    # 7. PRZEWOŹNIK (PrestaShop domyślnie ma dostawę przed płatnością)
    print("7. Wybór przewoźnika...")
    try:
        # Czekamy aż sekcja dostawy będzie aktywna
        wait.until(EC.element_to_be_clickable((By.NAME, "confirmDeliveryOption")))
        
        delivery_options = driver.find_elements(By.CSS_SELECTOR, ".delivery-option input")
        # Wybór jednego z dwóch (jeśli są min. 2, bierzemy drugi, jeśli nie, pierwszy)
        if len(delivery_options) >= 2:
            driver.execute_script("arguments[0].click();", delivery_options[1])
            print("   Wybrano przewoźnika nr 2.")
        elif delivery_options:
            driver.execute_script("arguments[0].click();", delivery_options[0])
            print("   Wybrano przewoźnika nr 1.")
            
        driver.find_element(By.NAME, "confirmDeliveryOption").click()
    except Exception as e:
        print(f"   ⚠️ Problem z przewoźnikiem: {e}")

    # 6. PŁATNOŚĆ - "Przy odbiorze"
    print("6. Wybór płatności (Przy odbiorze)...")
    try:
        wait.until(EC.presence_of_element_located((By.ID, "payment-confirmation")))
        
        # Szukamy opcji zawierającej tekst "Cash on delivery" lub "przy odbiorze"
        payment_labels = driver.find_elements(By.CSS_SELECTOR, ".payment-option label")
        found_cod = False
        
        for label in payment_labels:
            text = label.text.lower()
            # Dostosuj te frazy do języka sklepu!
            if "cash" in text or "odbior" in text or "delivery" in text:
                radio_id = label.get_attribute("for")
                radio_btn = driver.find_element(By.ID, radio_id)
                driver.execute_script("arguments[0].click();", radio_btn)
                found_cod = True
                print(f"   ✅ Wybrano płatność: {label.text}")
                break
        
        if not found_cod:
            print("   ⚠️ Nie znaleziono 'Płatności przy odbiorze'. Wybieram pierwszą dostępną.")
            payment_inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='payment-option']")
            if payment_inputs:
                driver.execute_script("arguments[0].click();", payment_inputs[0])
        
        # Checkbox regulaminu
        conditions_checkbox = driver.find_element(By.CSS_SELECTOR, "input[id*='conditions_to_approve']")
        driver.execute_script("arguments[0].click();", conditions_checkbox)
    except Exception as e:
        print(f"   Problem z płatnością: {e}")

    # 8. ZATWIERDZENIE
    print("8. Zatwierdzanie zamówienia...")
    try:
        place_order_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#payment-confirmation button")))
        place_order_btn.click()
        print("   ✅ Kliknięto 'Zamawiam'.")
    except Exception as e:
        print(f"   ⚠️ Nie udało się kliknąć 'Zamawiam': {e}")

    # 9. STATUS
    print("9. Sprawdzanie statusu...")
    # Czekamy na potwierdzenie zamówienia na ekranie
    try:
        wait.until(EC.url_contains("controller=order-confirmation"))
        print("   Jesteśmy na stronie potwierdzenia.")
    except TimeoutException:
        print("   ⚠️ Brak przekierowania na potwierdzenie, sprawdzam historię ręcznie.")

    driver.get(BASE_URL + "/index.php?controller=history")
    
    try:
        # Pobieramy pierwszy wiersz historii
        row = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "tbody tr:first-child")))
        status = row.find_element(By.CSS_SELECTOR, ".label-pill").text
        order_ref = row.find_element(By.CSS_SELECTOR, "th").text
        print(f"   ✅ Ostatnie zamówienie: {order_ref}, Status: {status}")
    except:
        print("   ⚠️ Nie udało się pobrać statusu.")

    # 10. FAKTURA
    print("10. Pobieranie faktury...")
    try:
        invoice_link = driver.find_element(By.CSS_SELECTOR, "tbody tr:first-child a[href*='pdf-invoice']")
        invoice_link.click()
        print("   ✅ Pobrano fakturę (sprawdź folder skryptu).")
        time.sleep(5) # Krótki czas na fizyczne zapisanie pliku
    except:
        print("   ⚠️ Brak faktury (czy status pozwala na pobranie?).")

    duration = time.time() - start_time
    print(f"--- TEST ZAKOŃCZONY W CZYM: {duration:.2f}s ---")

except Exception as e:
    print(f"KRYTYCZNY BŁĄD SKRYPTU: {e}")
    driver.save_screenshot("critical_error.png")

finally:
    driver.quit()