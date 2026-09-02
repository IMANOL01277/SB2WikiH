import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database", timeout=30)
soup = BeautifulSoup(resp.text, "lxml")

print("--- Headings ---")
for h in soup.find_all(['h2', 'h3']):
    print(h.name, h.get_text().strip())

print("\n--- Tables ---")
for t in soup.find_all('table'):
    # find previous heading
    prev = t.find_previous(['h2', 'h3'])
    print("Table after:", prev.get_text().strip() if prev else "None")
