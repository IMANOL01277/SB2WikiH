import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
soup = BeautifulSoup(resp.content, "lxml")

# Look for Cargo API calls or interactive widget config
# Method 1: look for any data-* in div/section elements
print("=== Elements with data attributes ===")
for el in soup.find_all(["div", "section", "template", "mw:ext"]):
    data_attrs = {k: v for k, v in el.attrs.items() if isinstance(k, str) and k.startswith("data-")}
    if data_attrs:
        print(f"<{el.name} data={list(data_attrs.keys())}>: {el.get_text()[:60]!r}")
        
# Method 2: look for Cargo or Scribunto
print()
print("=== Script content looking for cargo/item/database ===")
for s in soup.find_all("script"):
    txt = s.string or ""
    if any(kw in txt.lower() for kw in ["cargo", "item", "database", "longsword", "greatsword"]) and len(txt) > 100:
        print(txt[:500])
        print("---")
