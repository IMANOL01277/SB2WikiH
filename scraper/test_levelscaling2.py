import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})

import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    candidates = [r for r in reader if r["category"] == "Weapon" and r["dmg_clean"] and not r["dmg_max"] and r["wiki_link"]]

# Revisar varios para encontrar los que tienen texto "based on level" o similar
for r in candidates[:30]:
    resp = scraper.get(r["wiki_link"], timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")
    for table in soup.find_all("table"):
        headers = [th.get_text().strip() for th in table.find_all("th")]
        if "Base Damage" in headers:
            idx = headers.index("Base Damage")
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if cells and idx < len(cells):
                    raw = cells[idx].get_text(separator=" ").strip()
                    if "level" in raw.lower() or "per" in raw.lower() or len(raw) > 30:
                        print(f"{r['name']}: {repr(raw)}")
