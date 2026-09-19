import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
soup = BeautifulSoup(resp.content, "lxml")

# Look for the Cargo API or interactive widget data
# Fandom item databases often use Cargo extension
print("=== ALL DIVS with data attributes ===")
for el in soup.find_all(True, attrs=lambda a: any(k.startswith("data-") for k in a.keys()) if a else False):
    data_attrs = {k: v for k, v in el.attrs.items() if k.startswith("data-")}
    if data_attrs:
        print(f"<{el.name} data={data_attrs}>: {el.get_text()[:60]!r}")
        print()
