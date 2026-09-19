import requests, sys
sys.stdout.reconfigure(encoding="utf-8")

# Fetch the item database JS data file
resp = requests.get("https://swordburst2.fandom.com/wiki/MediaWiki:ItemDatabase2.js?action=raw&ctype=text/javascript", timeout=30)
print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
print("=== First 3000 chars ===")
print(resp.text[:3000])
print()
print("=== Last 500 chars ===")
print(resp.text[-500:])
