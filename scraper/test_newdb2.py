import cloudscraper
from bs4 import BeautifulSoup

# Try with different browser config
for config in [
    {"browser": "chrome", "platform": "windows", "mobile": False},
    {"browser": "firefox", "platform": "windows", "mobile": False},
    {"browser": "chrome", "platform": "linux", "mobile": False},
]:
    try:
        scraper = cloudscraper.create_scraper(browser=config)
        resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
        soup = BeautifulSoup(resp.text, "lxml")
        content = soup.find("div", class_="mw-parser-output")
        if content:
            print(f"SUCCESS with config: {config}")
            print(content.get_text(separator="\n")[:2000])
            break
        else:
            print(f"FAILED with config: {config} | status: {resp.status_code} | snippet: {resp.text[:100]}")
    except Exception as e:
        print(f"ERROR with config: {config}: {e}")
