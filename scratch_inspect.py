"""
Test: usar action=parse con rvslots para ver si hay un formato más eficiente,
o usar action=query&generator=categorymembers para obtener múltiples páginas.
También probar concurrent requests para ver velocidad.
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def parse_clean_max(cell_html_str):
    """Parsea una celda que puede tener 'Clean: X<p>Max: Y</p>' o simplemente 'X'."""
    soup = BeautifulSoup(cell_html_str, 'lxml')
    cell = soup.find('td')
    if not cell:
        return '', ''
    
    # Buscar patron data-source="dmg" o data-source="def"
    full_text = cell.get_text(' ', strip=True)
    
    m = re.search(r'clean[:\s]+([\d,.]+).*?max[:\s]+([\d,.]+)', full_text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).replace(',', ''), m.group(2).replace(',', '')
    
    # Solo un numero
    nums = re.findall(r'[\d,.]+', full_text)
    if nums:
        return nums[0].replace(',', ''), ''
    
    return full_text.strip(), ''

def fetch_item_stats(item_name):
    """Obtiene clean y max de dmg/def desde la página individual del item."""
    page = item_name.replace(' ', '_')
    url = f'https://swordburst2.fandom.com/api.php?action=parse&page={page}&format=json'
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        data = r.json()
        if 'error' in data:
            return item_name, '', '', '', ''
        html = data['parse']['text']['*']
        soup = BeautifulSoup(html, 'lxml')
        
        dmg_clean, dmg_max = '', ''
        def_clean, def_max = '', ''
        
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if 'base damage' in headers:
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    for cell in cells:
                        src = cell.get('data-source', '')
                        if src == 'dmg':
                            full = cell.get_text(' ', strip=True)
                            m = re.search(r'clean[:\s]+([\d,.]+).*?max[:\s]+([\d,.]+)', full, re.IGNORECASE | re.DOTALL)
                            if m:
                                dmg_clean = m.group(1).replace(',', '')
                                dmg_max = m.group(2).replace(',', '')
                            else:
                                dmg_clean = re.sub(r'[^\d.,]', '', full)
            elif 'defense' in headers:
                for row in table.find_all('tr'):
                    cells = row.find_all('td')
                    for cell in cells:
                        src = cell.get('data-source', '')
                        if src == 'def':
                            full = cell.get_text(' ', strip=True)
                            m = re.search(r'clean[:\s]+([\d,.]+).*?max[:\s]+([\d,.]+)', full, re.IGNORECASE | re.DOTALL)
                            if m:
                                def_clean = m.group(1).replace(',', '')
                                def_max = m.group(2).replace(',', '')
                            else:
                                def_clean = re.sub(r'[^\d.,]', '', full)
        
        return item_name, dmg_clean, dmg_max, def_clean, def_max
    except Exception as e:
        return item_name, '', '', '', str(e)

# Test con 10 items concurrentes y medir tiempo
items = ['Steel_Longsword', 'Novice_Armor', 'Crystalline', 'Wolf_Leather_Armor',
         'Leek', 'Coal_Miner_Clothes', 'Blade_of_Grass', 'Light_Fields_Armor',
         'Rock', 'Rapier_of_Flames']

start = time.time()
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(fetch_item_stats, item): item for item in items}
    for f in as_completed(futures):
        name, dc, dm, dfc, dfm = f.result()
        print(f'{name}: dmg_clean={dc!r} dmg_max={dm!r} | def_clean={dfc!r} def_max={dfm!r}')

elapsed = time.time() - start
print(f'\nTiempo: {elapsed:.1f}s para {len(items)} items')
print(f'Estimado para 1700 items con 20 workers: {1700/20 * (elapsed/len(items)):.0f}s')
