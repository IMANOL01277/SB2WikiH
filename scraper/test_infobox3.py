import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Desert_Storm", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

for el in soup.find_all('div', class_='pi-data'):
    label = el.find('h3', class_='pi-data-label')
    value = el.find('div', class_='pi-data-value')
    if label and value:
        print(f"{label.get_text().strip()}: {value.get_text().strip()}")
