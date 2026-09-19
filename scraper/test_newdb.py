import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

content = soup.find("div", class_="mw-parser-output")
if not content:
    print("No mw-parser-output found")
    print(soup.text[:500])
else:
    # Print first 3000 chars of text
    print(content.get_text(separator="\n")[:3000])
