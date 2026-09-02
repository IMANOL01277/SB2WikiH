import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Desert_Storm", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

for aside in soup.find_all('aside', class_='portable-infobox'):
    for div in aside.find_all('div', class_='pi-item'):
        print(div.get_text().strip())
