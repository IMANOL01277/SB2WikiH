import requests, sys, re, json
sys.stdout.reconfigure(encoding="utf-8")

resp = requests.get("https://swordburst2.fandom.com/api.php", params={
    "action": "parse",
    "page": "MediaWiki:ItemDatabase2.js",
    "prop": "wikitext",
    "format": "json"
})
js = resp.json().get("parse", {}).get("wikitext", {}).get("*", "")

# Save the full JS to disk
with open("scraper/itemdb_raw.js", "w", encoding="utf-8") as f:
    f.write(js)
    
# Look for the item data structure - search for JSON-like arrays or objects
# Look for pattern like "var items" or "window.items" or "[{"name":"
patterns = [
    r"var\s+\w*[Ii]tem[Ss]?\w*\s*=\s*(\[|\{)",
    r"window\.\w*[Ii]tem[Ss]?\w*\s*=\s*(\[|\{)",
    r"database\s*=\s*(\{|\[)",
    r"getDatabase",
    r"itemData",
]
for p in patterns:
    m = re.search(p, js)
    if m:
        pos = m.start()
        print(f"Pattern {p!r} found at pos {pos}:")
        print(js[pos:pos+200])
        print("---")
