import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})

# Test con varios tipos: arma, armadura, accesorio
for url in [
    "https://swordburst2.fandom.com/wiki/Desert_Storm",
    "https://swordburst2.fandom.com/wiki/Dragon_Heart",
    "https://swordburst2.fandom.com/wiki/Ethereal_Edge",
]:
    resp = scraper.get(url, timeout=30)
    soup = BeautifulSoup(resp.text, "lxml")
    content = soup.find("div", {"class": "mw-parser-output"})
    if not content:
        content = soup

    # Buscar tablas dentro del articulo
    for table in content.find_all("table"):
        headers = [th.get_text().strip() for th in table.find_all("th")]
        rows_text = []
        for row in table.find_all("tr"):
            cells = row.find_all(["td","th"])
            row_texts = [c.get_text().strip() for c in cells]
            if any(t for t in row_texts):
                rows_text.append(row_texts)
        print(f"URL: {url}")
        print(f"  Headers: {headers}")
        print(f"  Rows sample: {rows_text[:3]}")
        print()
