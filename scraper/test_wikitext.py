import requests, sys, json

# encoding fix
sys.stdout.reconfigure(encoding="utf-8")

base = "https://swordburst2.fandom.com"
resp = requests.get(f"{base}/api.php", params={
    "action": "parse",
    "page": "Item_Database_(New)",
    "prop": "wikitext",
    "format": "json"
})
data = resp.json()
wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
print(f"Wikitext length: {len(wikitext)}")
print(wikitext[:5000])
