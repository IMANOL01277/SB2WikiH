with open("scraper/wiki_scraper.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('"base_dmg":', '"dmg_clean":')
c = c.replace('"max_dmg":', '"dmg_max":')
c = c.replace('"base_def":', '"def_clean":')
c = c.replace('"max_def":', '"def_max":')
c = c.replace('.get("base_dmg"', '.get("dmg_clean"')
c = c.replace('.get("max_dmg"', '.get("dmg_max"')
c = c.replace('.get("base_def"', '.get("def_clean"')
c = c.replace('.get("max_def"', '.get("def_max"')

with open("scraper/wiki_scraper.py", "w", encoding="utf-8") as f:
    f.write(c)

print("Hecho")
