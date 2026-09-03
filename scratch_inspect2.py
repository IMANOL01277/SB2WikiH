"""
Verificar casos de Traveling_Salesman y Conquerer's_Wish.
"""
import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch_api(page):
    r = requests.get(
        f'https://swordburst2.fandom.com/api.php?action=parse&page={page}&format=json',
        headers=HEADERS, timeout=15
    )
    data = r.json()
    if 'error' in data:
        return None, data['error']['code']
    soup = BeautifulSoup(data['parse']['text']['*'], 'lxml')
    return soup, None

# Traveling Salesman - probar distintos nombres
for name in ['Traveling_Salesman', 'Traveling Salesman', 'Traveller%27s_Armor']:
    soup, err = fetch_api(name)
    if err:
        print(f"ERROR {name}: {err}")
    else:
        tables = soup.find_all('table')
        for i, t in enumerate(tables):
            headers = [th.get_text(strip=True) for th in t.find_all('th')]
            if 'Defense' in headers or 'Defence' in headers:
                for row in t.find_all('tr'):
                    for c in row.find_all('td'):
                        if c.get('data-source') in ('dmg', 'def'):
                            print(f"  {name} -> data-source={c.get('data-source')!r}: {c.get_text(' ', strip=True)!r}")
        # Print title
        title = soup.find('h1')
        if title:
            print(f"  Title: {title.get_text(strip=True)!r}")

print()

# Conquerer's Wish
for name in ["Conquerer's_Wish", "Conquerers_Wish", "Conqueror%27s_Wish", "Conqueror's_Wish"]:
    soup, err = fetch_api(name)
    if err:
        print(f"ERROR {name}: {err}")
    else:
        title = soup.find('h1')
        if title:
            print(f"  Found: {title.get_text(strip=True)!r}")
        for t in soup.find_all('table'):
            headers = [th.get_text(strip=True) for th in t.find_all('th')]
            if 'Defense' in headers or 'Defence' in headers:
                for row in t.find_all('tr'):
                    for c in row.find_all('td'):
                        if c.get('data-source') in ('def',):
                            print(f"    def: {c.get_text(' ', strip=True)!r}")

print()
# Ver cuantos items sin wiki_link hay
print("Checking items without wiki_link from scraper...")
import sys
sys.path.insert(0, '.')
import logging
logging.basicConfig(level=logging.WARNING)
from scraper.wiki_scraper import scrape_item_database

# Ya no re-ejecutamos, usamos datos anteriores rápidos
# Ver el patrón de items que tienen page missing
