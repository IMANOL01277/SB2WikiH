import requests

url = "https://docs.google.com/spreadsheets/d/1EZkeyhJGaWuai37KfjvrMOiVCmjhmf6m0AJ-cvbzCGI/export?format=csv&gid=780998096"
resp = requests.get(url)
print("Aura prices CSV preview:")
print("\n".join(resp.text.split("\n")[:20]))
