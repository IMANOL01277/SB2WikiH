import sys, re
sys.stdout.reconfigure(encoding="utf-8")

with open("scraper/itemdb_raw.js", encoding="utf-8") as f:
    js = f.read()

# Find the getDatabase function to understand how items are fetched
m = re.search(r"function\s+getDatabase\s*\([^)]*\)\s*\{", js)
if m:
    pos = m.start()
    print("getDatabase found at:", pos)
    print(js[pos:pos+2000])
