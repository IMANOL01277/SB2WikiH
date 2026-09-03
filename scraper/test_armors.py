import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    armors = [r for r in reader if r["category"] == "Armor"]
    armors_with_def = [r for r in armors if r["def_clean"]]
    
print(f"Total Armors: {len(armors)}")
print(f"Armors with def_clean: {len(armors_with_def)}")
if len(armors) > len(armors_with_def):
    print("Armors WITHOUT def_clean (first 10):")
    for r in [r for r in armors if not r["def_clean"]][:10]:
        print(f"  {r['name']} - link: {r['wiki_link']}")
