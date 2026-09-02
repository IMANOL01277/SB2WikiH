import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

table = soup.find_all('table')[1] # Second table is the items table
row = table.find_all('tr')[1]
for i, td in enumerate(row.find_all('td')):
    print(f"TD {i}:", td)
