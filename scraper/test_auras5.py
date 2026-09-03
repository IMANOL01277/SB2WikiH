import cloudscraper
from bs4 import BeautifulSoup
import re

def scrape_auras():
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
    resp = scraper.get("https://swordburst2.fandom.com/wiki/Auras", timeout=20)
    soup = BeautifulSoup(resp.text, "lxml")

    auras = []
    
    # Skip the first table (table of contents)
    tables = soup.find_all("table")
    for i, table in enumerate(tables):
        if i == 0:
            continue
            
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue
            
        # We need to find the row that has the names. Usually it has font-weight: bold
        name_row = None
        rarity_row = None
        image_row = None
        
        for idx, row in enumerate(rows):
            style = row.get("style", "")
            if "font-weight: bold" in style or "font-weight:bold" in style:
                name_row = row
                if idx > 0:
                    image_row = rows[idx-1]
                if idx + 1 < len(rows):
                    rarity_row = rows[idx+1]
                break
                
        if not name_row:
            # Fallback: second row is usually names if length >=3 and first row is images
            if len(rows) >= 3:
                image_row = rows[0]
                name_row = rows[1]
                rarity_row = rows[2]
                
        if name_row:
            name_cells = name_row.find_all(["td", "th"])
            img_cells = image_row.find_all(["td", "th"]) if image_row else []
            rarity_cells = rarity_row.find_all(["td", "th"]) if rarity_row else []
            
            # The first cell might be a rowspan for the chest.
            # Names are usually straight text.
            for j, cell in enumerate(name_cells):
                name = cell.get_text(separator=" ").strip()
                if not name or "Aura Chest" in name:
                    continue
                    
                # Try to get rarity
                rarity = ""
                if j < len(rarity_cells):
                    rarity = rarity_cells[j].get_text(separator=" ").strip()
                    if not rarity and j+1 < len(rarity_cells):
                         # offset by 1 if there's a rowspan chest
                         rarity = rarity_cells[j+1].get_text(separator=" ").strip()
                
                # Cleanup rarity text
                if "Drop Chance" in rarity:
                    rarity = ""
                rarity = re.sub(r"Drop.*", "", rarity, flags=re.IGNORECASE).strip()
                
                # Image
                # Images in fandom can be data-src or src inside img
                # Need to match column index, accounting for rowspan on the left
                auras.append({"name": name, "rarity": rarity, "category": "Aura"})
                
    return auras

auras = scrape_auras()
print(f"Scraped {len(auras)} auras.")
print("Sample:")
for a in auras[:10]:
    print(a)
