import json
import sys
sys.path.insert(0, '.')
from scraper.wiki_scraper import scrape_item_database

items = scrape_item_database()
print(f'Total items: {len(items)}')

# Vamos a simular las lineas de CSV si el index empezara en 1, 
# o simplemente vamos a buscar los items alrededor del indice 1560-1610
print("\nItems in range 1560 - 1610:")
for i in range(1560, min(1610, len(items))):
    item = items[i]
    print(f"[{i}] {item['name']} | Type: {item['category']} | DefClean: {item.get('def_clean')} | DmgClean: {item.get('dmg_clean')}")

armors = [i for i in items if i['category'] == 'Armor']
print(f'\nTotal armaduras: {len(armors)}')

print('\nArmaduras con def_clean vacío (deberia ser 0):')
missing = [a for a in armors if not a.get('def_clean')]
for a in missing:
    print(f"{a['name']} | wiki={a['wiki_link']}")
