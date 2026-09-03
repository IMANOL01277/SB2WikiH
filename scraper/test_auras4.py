import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Auras", timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

tables = soup.find_all("table")
for i, table in enumerate(tables):
    if i == 18:
        print(table.prettify())
        break
