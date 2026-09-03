import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Auras", timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

tables = soup.find_all("table")
for i, table in enumerate(tables):
    rows = table.find_all("tr")
    if len(rows) > 2:
        cells = [c.get_text(separator=" ").strip() for c in rows[1].find_all(["td", "th"])]
        if len(cells) >= 2:
            print(f"Table {i}, headers?: {cells}")
