import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

# Get ALL scripts loaded on the page, find the item-database-app bundle
import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
resp = scraper.get("https://swordburst2.fandom.com/wiki/Item_Database_(New)", timeout=30)
soup = BeautifulSoup(resp.content, "lxml")

print("=== ALL SCRIPT SRC ===")
for s in soup.find_all("script", src=True):
    src = s.get("src", "")
    if any(kw in src.lower() for kw in ["item", "database", "app", "wiki"]):
        print(src)
        
print()
print("=== ALL LINK HREF (stylesheets / resources) ===")
for l in soup.find_all("link", href=True):
    href = l.get("href", "")
    if any(kw in href.lower() for kw in ["item", "database", "app"]):
        print(href)
        
# Also look for the raw wikitext for module references
resp2 = requests.get("https://swordburst2.fandom.com/api.php", params={
    "action": "parse",
    "page": "Item_Database_(New)",
    "prop": "wikitext",
    "format": "json"
})
wikitext = resp2.json().get("parse", {}).get("wikitext", {}).get("*", "")
import re
# Find any Module: references
modules = re.findall(r"Module:[^\|}\n]+", wikitext)
print("\n=== MODULES referenced ===")
for m in set(modules):
    print(m)

# Find any template calls that might include item data  
templates = re.findall(r"\{\{[^}]{1,80}\}\}", wikitext)
print("\n=== TEMPLATES ===")
for t in set(templates[:30]):
    print(t)
