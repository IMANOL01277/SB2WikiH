import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    auras = [r for r in reader if r["category"] == "Aura" and r["price_clean_oml"]]

print(f"Total auras con precio emparejado: {len(auras)}")
print("Ejemplos:")
for a in auras[:10]:
    print(f"  Aura: {a['name']:<25} | Rareza: {a['rarity']:<10} | Precio: {a['price_clean_oml']} OML")
