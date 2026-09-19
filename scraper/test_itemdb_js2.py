import cloudscraper, sys
sys.stdout.reconfigure(encoding="utf-8")

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/MediaWiki:ItemDatabase2.js?action=raw&ctype=text/javascript", timeout=30)
print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
print(resp.text[:5000])
