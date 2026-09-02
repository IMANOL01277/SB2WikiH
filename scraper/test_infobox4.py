import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Desert_Storm", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

text = soup.get_text(separator=' | ')
match = re.search(r'.{0,50}Max.{0,50}', text, re.IGNORECASE)
if match:
    print("Match:", match.group(0))
