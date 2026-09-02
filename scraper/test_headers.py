import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

print("Tables headers on main page:")
for i, table in enumerate(soup.find_all('table')):
    headers = [th.get_text().strip() for th in table.find_all('th')]
    if headers and "Damage" in headers:
        print(f"Table {i} headers: {headers}")
