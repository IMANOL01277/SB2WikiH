import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("Columns:", reader.fieldnames)
    rows = list(reader)
    print("Row 0:", rows[0])
    
    # check one longsword, one armor, one aura
    for category in ["Longsword", "Armor", "Aura"]:
        item = next((r for r in rows if r["category"] == category), None)
        if item:
            print(f"\n{category}: {item['name']} | Upgradeable: {item['upgradeable']} | Rarity: {item['rarity']} | DMG Clean: {item['dmg_clean']} | DEF Clean: {item['def_clean']} | Image: {item['image_url']}")
