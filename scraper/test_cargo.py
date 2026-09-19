import requests
import json

# Try the Fandom Cargo API
base = "https://swordburst2.fandom.com"
params = {
    "action": "cargoquery",
    "format": "json",
    "tables": "Weapons",
    "fields": "_pageName,Name,Level,Damage,Crit,Rarity,Type,Obtain",
    "limit": 10
}
resp = requests.get(f"{base}/api.php", params=params)
print("Cargo Weapons:", resp.status_code, resp.text[:500])

# Try different table names
for table in ["Items", "Weapons", "ItemDatabase", "Item", "Equipment", "Longswords"]:
    params["tables"] = table
    r = requests.get(f"{base}/api.php", params=params)
    data = r.json()
    if "error" not in data:
        print(f"TABLE {table}: HIT! {r.text[:300]}")
    else:
        err = data.get("error", {}).get("info", "")
        if "does not exist" not in err.lower():
            print(f"TABLE {table}: {err[:100]}")
