import cloudscraper
from bs4 import BeautifulSoup
import json, re

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
soup = BeautifulSoup(resp.content, "lxml")

# Look for any script tags or data-* attributes that might hold the item data
scripts = soup.find_all("script")
for i, s in enumerate(scripts):
    txt = s.string or ""
    if "longsword" in txt.lower() or "item" in txt.lower() and len(txt) > 500:
        print(f"Script {i}: {txt[:300]}")
        print("---")

# Also look for data-mw, data-item, or any widgets
for el in soup.find_all(attrs={"data-mw": True}):
    print("data-mw:", el.get("data-mw", "")[:200])
    print()

# Look for any element with "card" or "widget" in class
for el in soup.find_all(class_=re.compile("card|widget|item|database", re.I)):
    print(f"<{el.name} class={el.get('class')}>: {el.get_text()[:100]!r}")
    print()
