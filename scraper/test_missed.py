import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

for table in soup.find_all("table"):
    h2 = table.find_previous("h2")
    if not h2:
        continue
    heading_text = h2.get_text().strip().lower()
    heading_key = re.sub(r"[^a-z]", "", heading_text)
    
    # How many items in this table?
    rows = len(table.find_all("tr")) - 1 # roughly
    
    print(f"Table under h2: '{heading_text}' (key: {heading_key}) -> rows: {rows}")
