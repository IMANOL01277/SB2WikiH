import csv

with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("Columnas:", list(rows[0].keys()))
print()

weapons = [r for r in rows if r["category"] == "Weapon" and r["dmg_clean"]][:8]
print(f"Armas con dmg_clean: {len([r for r in rows if r['dmg_clean']])}")
print(f"Armas con dmg_max:   {len([r for r in rows if r['dmg_max']])}")
for r in weapons:
    print(f"  {r['name']:<30} Lv:{r['level']:<3} Clean:{r['dmg_clean']:<6} Max:{r['dmg_max']:<6} Crit:{r['crit']}")

print()
armors = [r for r in rows if r["category"] == "Armor" and r["def_clean"]][:5]
print(f"Armaduras con def_clean: {len([r for r in rows if r['def_clean']])}")
for r in armors:
    print(f"  {r['name']:<30} Clean:{r['def_clean']:<6} Max:{r['def_max']:<6}")

print()
priced = [r for r in rows if r["price_clean_oml"]][:5]
print(f"Items con precio: {len([r for r in rows if r['price_clean_oml']])}")
for r in priced:
    print(f"  {r['name']:<30} CleanOML:{r['price_clean_oml']:<8} MaxOML:{r['price_max_oml']:<8}")

print()
print(f"TOTAL ITEMS: {len(rows)}")
