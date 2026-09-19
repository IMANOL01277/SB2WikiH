import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
soup = BeautifulSoup(resp.content, "lxml")  # Use .content (bytes) instead of .text to avoid encoding error

content = soup.find("div", class_="mw-parser-output")
if content:
    print("Found mw-parser-output!")
    # Print structure overview
    for child in content.children:
        tag = getattr(child, "name", None)
        if tag:
            cls = child.get("class", [])
            print(f"  <{tag} class={cls}>: {child.get_text()[:80]!r}")
else:
    print("Not found")
    print(soup.get_text()[:500])
