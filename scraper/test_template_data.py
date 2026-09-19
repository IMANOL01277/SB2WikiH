import requests, sys, json
sys.stdout.reconfigure(encoding="utf-8")

resp = requests.get("https://swordburst2.fandom.com/api.php", params={
    "action": "query",
    "prop": "revisions",
    "rvprop": "content",
    "rvslots": "main",
    "titles": "Template:ItemDatabaseDataTest",
    "formatversion": "2",
    "format": "json"
})
data = resp.json()
page = data["query"]["pages"][0]
text = page["revisions"][0]["slots"]["main"]["content"]

# Remove <pre> tags if present
text = text.strip()
if text.startswith("<pre>"):
    text = text[5:]
if text.endswith("</pre>"):
    text = text[:-6]
text = text.strip()

print(f"Content length: {len(text)}")
print("First 2000 chars:")
print(text[:2000])
