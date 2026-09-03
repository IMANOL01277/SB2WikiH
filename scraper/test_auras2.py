import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Auras", timeout=20)
soup = BeautifulSoup(resp.text, "lxml")

tables = soup.find_all("table")
if tables:
    print(tables[0].prettify()[:1000])
    print("---")
    rows = tables[0].find_all("tr")
    for r in rows:
        print([c.get_text(separator=" ").strip() for c in r.find_all(["td", "th"])])
