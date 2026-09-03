import re
import traceback

def parse_auras(soup):
    auras = []
    tables = soup.find_all("table")
    for i, table in enumerate(tables):
        if i == 0:
            continue # skip TOC
            
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
            
        name_row, image_row, rarity_row = None, None, None
        
        for idx, row in enumerate(rows):
            style = row.get("style", "")
            # Fandom auras typically bold the name row
            if "font-weight: bold" in style or "font-weight:bold" in style:
                name_row = row
                if idx > 0:
                    image_row = rows[idx-1]
                if idx + 1 < len(rows):
                    rarity_row = rows[idx+1]
                break
                
        # Fallback if no style found
        if not name_row and len(rows) >= 3:
            # Usually row 0 is image, row 1 is name, row 2 is rarity
            image_row = rows[0]
            name_row = rows[1]
            rarity_row = rows[2]
            
        if not name_row:
            continue
            
        name_cells = name_row.find_all(["td", "th"])
        img_cells = image_row.find_all(["td", "th"]) if image_row else []
        rarity_cells = rarity_row.find_all(["td", "th"]) if rarity_row else []
        
        # We assume the images cell and name cell match in index, except if there's a rowspan on the left.
        # Fandom chest image takes up td[0] with rowspan=5, so aura images start at td[1].
        # But in the name row, the chest td is already accounted for by rowspan, so name_cells[0] is the first aura name.
        
        for j, cell in enumerate(name_cells):
            name = cell.get_text(separator=" ").strip()
            if not name or "Aura Chest" in name:
                continue
                
            # Rarity is directly below the name, so index j should match
            rarity = ""
            if rarity_row and j < len(rarity_cells):
                rarity = rarity_cells[j].get_text(separator=" ").strip()
            
            # Clean up rarity
            if "Drop Chance" in rarity or "Legendary" not in rarity and "Rare" not in rarity and "Uncommon" not in rarity and "Common" not in rarity:
                # sometimes rarity row is actually the 3rd row, sometimes it's nested
                rarity_clean = re.sub(r"Drop.*", "", rarity, flags=re.IGNORECASE).strip()
                if not rarity_clean:
                    # try getting it from the div inside the cell
                    divs = rarity_cells[j].find_all("div") if j < len(rarity_cells) else []
                    for d in divs:
                        t = d.get_text(separator=" ").strip()
                        if t in ["Common", "Uncommon", "Rare", "Legendary"]:
                            rarity_clean = t
                            break
                rarity = rarity_clean

            # Normalize missing rarities
            if rarity not in ["Common", "Uncommon", "Rare", "Legendary"]:
                if rarity:
                    # Attempt to extract if stuck with other text
                    m = re.search(r"(Common|Uncommon|Rare|Legendary)", rarity, re.I)
                    if m:
                        rarity = m.group(1).capitalize()
                    else:
                        rarity = "Legendary" # default assumption for auras if unknown
                else:
                    rarity = "Legendary"
                
            img_url = ""
            # Image row has a rowspan on the left, so we offset by 1 if j+1 < len(img_cells)
            img_idx = j + 1 if len(img_cells) > len(name_cells) else j
            if image_row and img_idx < len(img_cells):
                img_tag = img_cells[img_idx].find("img")
                if img_tag:
                    img_url = img_tag.get("data-src") or img_tag.get("src") or ""
                    img_url = img_url.split("/revision")[0] if "/revision" in img_url else img_url
                    if img_url.startswith("data:image"):
                        img_url = ""
                        
            # Use a dummy wiki_link so the CSV has a link, even if individual aura pages might not exist/be needed
            wiki_name = name.replace(" ", "_")
            wiki_link = f"https://swordburst2.fandom.com/wiki/{wiki_name}"
            
            auras.append({
                "name": name,
                "category": "Aura",
                "rarity": rarity,
                "level": "",
                "dmg_clean": "",
                "dmg_max": "",
                "def_clean": "",
                "def_max": "",
                "upgradeable": "FALSE",
                "crit": "",
                "health_regen": "",
                "stamina_regen": "",
                "obtain": "",
                "image_link": img_url,
                "wiki_link": wiki_link
            })
            
    return auras

print("Function prepared.")
