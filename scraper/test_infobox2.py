import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Desert_Storm", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

for el in soup.find_all(string=re.compile("Max", re.IGNORECASE)):
    parent = el.parent
    print(parent.get_text().strip())
