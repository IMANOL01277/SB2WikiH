import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Auras", timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

for table in soup.find_all("table"):
    headers = [th.get_text().strip() for th in table.find_all("th")]
    print(f"Aura table headers: {headers}")
