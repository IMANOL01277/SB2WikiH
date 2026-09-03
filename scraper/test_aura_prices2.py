from scraper.price_scraper import download_sheet, parse_sheet

csv_text = download_sheet("auras", 780998096)
items = parse_sheet("auras", csv_text)

print(f"Parsed {len(items)} items from auras sheet.")
for k, v in list(items.items())[:10]:
    print(f"{k}: {v}")
