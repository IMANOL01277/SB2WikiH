import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    scaling_weapons = [r for r in reader if "level" in r["dmg_clean"].lower()]

print(f"Encontradas {len(scaling_weapons)} armas que escalan por nivel.")
print("Ejemplos:")
for w in scaling_weapons[:10]:
    print(f"  Nombre: {w['name']:<20} | Upgradeable: {w['upgradeable']:<5} | Dmg: {w['dmg_clean']}")
