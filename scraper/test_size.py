import csv
with open("SB2ItemDB.csv", encoding="utf-8") as f:
    data = f.read()
    
# Count how much we save by stripping the base url
reduced = data.replace("https://swordburst2.fandom.com/Special:Redirect/file/", "")
reduced = reduced.replace("https://swordburst2.fandom.com/wiki/", "")

print(f"Original size: {len(data)}")
print(f"Reduced size: {len(reduced)}")
