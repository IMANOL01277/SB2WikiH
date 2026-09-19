import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

# Try the API action=raw with the parse API instead - goes through MediaWiki, not direct URL
resp = requests.get("https://swordburst2.fandom.com/api.php", params={
    "action": "parse",
    "page": "MediaWiki:ItemDatabase2.js",
    "prop": "wikitext",
    "format": "json"
})
d = resp.json()
wikitext = d.get("parse", {}).get("wikitext", {}).get("*", "")
print(f"Length: {len(wikitext)}")
print(wikitext[:5000])
