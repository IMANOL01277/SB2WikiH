import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

# The item-database-app div is a React app. Check the wiki JS pages that load extra scripts.
# Look at the MediaWiki ResourceLoader for this wiki
resp = requests.get("https://swordburst2.fandom.com/api.php", params={
    "action": "query",
    "list": "allpages",
    "apnamespace": "2000",  # Gadgets/JS namespace
    "format": "json",
    "aplimit": 50
})
print("NS 2000:", resp.json())

# Try MediaWiki namespace (8)
resp2 = requests.get("https://swordburst2.fandom.com/api.php", params={
    "action": "query",
    "list": "allpages",
    "apnamespace": "8",
    "apprefix": "Common",
    "format": "json",
    "aplimit": 10
})
print("NS 8 Common:", resp2.json())

# Look for wiki common.js or specific item-database JS modules
for page in ["MediaWiki:Common.js", "MediaWiki:Item-database-app.js", "MediaWiki:Gadget-item-database.js"]:
    r = requests.get("https://swordburst2.fandom.com/api.php", params={
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json"
    })
    d = r.json()
    if "error" not in d:
        wt = d.get("parse", {}).get("wikitext", {}).get("*", "")
        print(f"\n=== {page} ===")
        print(wt[:1000])
