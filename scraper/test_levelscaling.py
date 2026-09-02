import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})

# Buscar armas que tengan dmg_clean pero no dmg_max en nuestro CSV (candidatos a level-scaling)
import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    candidates = [r for r in reader if r["category"] == "Weapon" and r["dmg_clean"] and not r["dmg_max"] and r["wiki_link"]]

print(f"Candidatos sin max_dmg: {len(candidates)}")
print("Primeros 5:")
for r in candidates[:5]:
    print(f"  {r['name']} - {r['wiki_link']}")

# Visitar la primera para ver el texto real
if candidates:
    url = candidates[0]["wiki_link"]
    print(f"\nVisitando: {url}")
    resp = scraper.get(url, timeout=20)
    soup = BeautifulSoup(resp.text, "lxml")
    for table in soup.find_all("table"):
        headers = [th.get_text().strip() for th in table.find_all("th")]
        if "Base Damage" in headers:
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if cells:
                    for i, h in enumerate(headers):
                        if h == "Base Damage" and i < len(cells):
                            raw = cells[i].get_text(separator=" ").strip()
                            print(f"  Raw Base Damage text: {repr(raw)}")
