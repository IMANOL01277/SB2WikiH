import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

for table in soup.find_all('table')[:2]:
    print("HEADERS:")
    for th in table.find_all('th'):
        print(th.get_text().strip())
    print("FIRST ROW:")
    row = table.find_all('tr')[1]
    for td in row.find_all('td'):
        print(td.get_text().strip())
    print("---")
