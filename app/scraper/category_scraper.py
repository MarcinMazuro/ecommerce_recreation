import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://www.dobreziele.pl/'

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response.encoding = 'utf-8'

    soup = BeautifulSoup(response.text, 'lxml')

    nav_menu = soup.find('div', class_='container hidden-xs')

    def scrape_categories_recursively(ul_element):
        if not ul_element:
            return []

        categories = []
        
        for child_tag in ul_element.find_all(recursive=False):
            
            lis_to_process = [] 
            
            if child_tag.name == 'li':
                lis_to_process.append(child_tag)
                
            elif child_tag.name == 'div':
                lis_to_process.extend(child_tag.find_all('li', recursive=False))
            
            for li in lis_to_process:
                link = li.find('a', recursive=False)
                if not link:
                    continue

                cat_name_node = link.contents[0]
                cat_name = cat_name_node.strip() if cat_name_node else ""
                cat_url = link.get('href', '#')

                if not cat_name: 
                    continue

                category_data = {
                    'name': cat_name,
                    'url': cat_url,
                    'subcategories': []
                }

                sub_ul = li.find('ul', recursive=False)
                category_data['subcategories'] = scrape_categories_recursively(sub_ul)
                
                categories.append(category_data)
                
        return categories

    categories_tree = scrape_categories_recursively(nav_menu.find('ul', recursive=False))
    output_path = Path(__file__).resolve().parent.parent / 'data' / 'categories.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(categories_tree, indent=2, ensure_ascii=False))
    print(f"Kategorie zostały zapisane do {output_path}")


except requests.RequestException as e:
        print(f"Błąd podczas pobierania {url}: {e}")
    
