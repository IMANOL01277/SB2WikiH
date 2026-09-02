for fname in ["scraper/merge.py", "scraper/item_page_scraper.py"]:
    with open(fname, "r", encoding="utf-8") as f:
        c = f.read()
    c = c.replace('"base_dmg"', '"dmg_clean"')
    c = c.replace('"max_dmg"', '"dmg_max"')
    c = c.replace('"base_def"', '"def_clean"')
    c = c.replace('"max_def"', '"def_max"')
    c = c.replace("'base_dmg'", "'dmg_clean'")
    c = c.replace("'max_dmg'", "'dmg_max'")
    c = c.replace("'base_def'", "'def_clean'")
    c = c.replace("'max_def'", "'def_max'")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"Actualizado: {fname}")
