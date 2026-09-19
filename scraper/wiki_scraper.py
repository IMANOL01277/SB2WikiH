"""
wiki_scraper.py
~~~~~~~~~~~~~~~
Obtiene todos los items del SwordBurst 2 Item Database
usando la API de MediaWiki, que retorna un JSON limpio desde
Template:ItemDatabaseDataTest en una sola peticion.
"""

import logging
import re
import json
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MEDIAWIKI_API = "https://swordburst2.fandom.com/api.php"
DATA_TEMPLATE  = "Template:ItemDatabaseDataTest"
FANDOM_BASE    = "https://swordburst2.fandom.com"

CATEGORY_KEYWORDS = {
    "longsword":     "Longsword",
    "greatsword":    "Greatsword",
    "katana":        "Katana",
    "rapier":        "Rapier",
    "spear":         "Spear",
    "scythe":        "Scythe",
    "armor":         "Armor",
    "accessory":     "Accessory",
    "accessories":   "Accessory",
    "companion":     "Companion",
    "pet":           "Companion",
    "body aura":     "Body Aura",
    "aura":          "Aura",
    "miscellaneous": "Miscellaneous",
    "misc":          "Miscellaneous",
}

SUBTYPE_STRIP_WORDS = {
    "longsword","greatsword","katana","rapier","spear","scythe",
    "armor","accessory","accessories","companion","pet",
    "aura","body aura","miscellaneous","misc",
}


def _clean(text) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _clean_wikilinks(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[File:[^\]]+\]\]", "", text)
    text = re.sub(r"\[\[Image:[^\]]+\]\]", "", text)
    text = re.sub(r"'{2,3}", "", text)
    text = re.sub(r"\{\{[^}]*\}\}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return _clean(text)


def _parse_category_subtype(type_str: str):
    raw = _clean(type_str).lower()
    category = "Miscellaneous"
    # Check "body aura" before "aura" so it takes priority
    for keyword in ["body aura", "longsword", "greatsword", "katana", "rapier",
                    "spear", "scythe", "armor", "accessory", "accessories",
                    "companion", "pet", "aura", "miscellaneous", "misc"]:
        if keyword in raw:
            category = CATEGORY_KEYWORDS[keyword]
            break

    subtype_text = type_str or ""
    for word in SUBTYPE_STRIP_WORDS:
        subtype_text = re.sub(re.escape(word), "", subtype_text, flags=re.IGNORECASE)
    subtype_text = _clean(subtype_text)
    subtype_text = re.sub(r"^\W+|\W+$", "", subtype_text).strip()
    return category, subtype_text


def _parse_stat(stat_str):
    """
    Parsea un campo de stat (dmg o def).
    Retorna (clean_val, max_val, upgradeable: bool).
    """
    if not stat_str:
        return "", "", False

    s = _clean(str(stat_str).replace("\n", " "))

    if re.search(r"per level|based on level|level based", s, re.I):
        formula = re.sub(r"Damage based on level\.?\s*", "", s, flags=re.I).strip()
        return formula, "", False

    m_clean = re.search(r"[Cc]lean\s*[:·]\s*([\d,]+)", s)
    m_max   = re.search(r"[Mm]ax\s*[:·]\s*([\d,]+)", s)

    if m_clean:
        clean = m_clean.group(1).replace(",", "")
        max_  = m_max.group(1).replace(",", "") if m_max else ""
        return clean, max_, bool(max_)

    m_single = re.search(r"([\d,]+)", s)
    if m_single:
        return m_single.group(1).replace(",", ""), "", True

    return s, "", False


def _parse_abilities(abilities_str: str):
    if not abilities_str:
        return "", ""
    m_h = re.search(r"([+\-]?\d+(?:\.\d+)?)\s*%?\s*Health\s*Reg", abilities_str, re.I)
    m_s = re.search(r"([+\-]?\d+(?:\.\d+)?)\s*%?\s*Stamina\s*Reg", abilities_str, re.I)
    return (m_h.group(1) + "%" if m_h else ""), (m_s.group(1) + "%" if m_s else "")


def _parse_rarity(rarity_str: str) -> str:
    if not rarity_str:
        return ""
    r = _clean(rarity_str)
    for k in ("Common","Uncommon","Rare","Legendary","Tribute","Burst","Dev"):
        if k.lower() == r.lower():
            return k
    return r


def _image_url(icon_filename: str) -> str:
    if not icon_filename:
        return ""
    name = re.sub(r"^(File:|Image:)", "", icon_filename, flags=re.I).strip()
    name = name.replace(" ", "_")
    return f"{FANDOM_BASE}/Special:Redirect/file/{name}"


def _wiki_url(item_name: str, category: str) -> str:
    if category in ("Aura", "Body Aura", "Companion"):
        return ""
    safe = item_name.replace(" ", "_")
    return f"{FANDOM_BASE}/wiki/{safe}"


def fetch_raw_json():
    logger.info(f"Descargando datos del wiki via MediaWiki API: {DATA_TEMPLATE}")
    try:
        resp = requests.get(MEDIAWIKI_API, params={
            "action":        "query",
            "prop":          "revisions",
            "rvprop":        "content|timestamp",
            "rvslots":       "main",
            "titles":        DATA_TEMPLATE,
            "formatversion": "2",
            "format":        "json",
        }, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        logger.error(f"Error descargando datos del wiki: {exc}")
        return None, ""

    data      = resp.json()
    page      = data.get("query", {}).get("pages", [{}])[0]
    revisions = page.get("revisions", [])
    if not revisions:
        logger.error("No se encontraron revisiones en " + DATA_TEMPLATE)
        return None, ""

    slot      = revisions[0].get("slots", {}).get("main", {})
    raw_text  = slot.get("content", "").strip()
    timestamp = revisions[0].get("timestamp", "")

    raw_text = re.sub(r"^<pre>", "", raw_text).strip()
    raw_text = re.sub(r"</pre>$", "", raw_text).strip()

    if not raw_text:
        logger.error("El template esta vacio")
        return None, ""

    try:
        parsed = json.loads(raw_text)
        logger.info(f"JSON descargado: {len(parsed)} entradas | ultima edicion wiki: {timestamp}")
        return parsed, timestamp
    except Exception as exc:
        logger.error(f"JSON invalido: {exc}")
        return None, ""


def scrape_item_database() -> list:
    raw_db, wiki_timestamp = fetch_raw_json()
    if not raw_db:
        return []

    items = []
    seen  = set()
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for idx, (key, raw) in enumerate(raw_db.items(), start=1):
        if not key or not isinstance(raw, dict):
            continue

        name = _clean(raw.get("name") or key)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        type_str          = _clean(raw.get("type", ""))
        category, subtype = _parse_category_subtype(type_str)
        rarity            = _parse_rarity(raw.get("rarity", ""))
        level             = _clean(raw.get("level", ""))

        dmg_clean, dmg_max, dmg_up = _parse_stat(raw.get("dmg"))
        def_clean, def_max, def_up = _parse_stat(raw.get("def"))

        if category in ("Aura", "Body Aura", "Companion", "Miscellaneous"):
            upgradeable = "FALSE"
        elif dmg_max or def_max:
            upgradeable = "TRUE"
        elif not dmg_up and not def_up:
            upgradeable = "FALSE"
        else:
            upgradeable = "TRUE"

        crit                      = _clean(raw.get("crit", ""))
        health_regen, stamina_regen = _parse_abilities(raw.get("abilities", ""))
        obtain                    = _clean_wikilinks(raw.get("obtain", ""))
        image_url                 = _image_url(raw.get("icon", ""))
        wiki_url                  = _wiki_url(name, category)

        items.append({
            "id":            idx,
            "name":          name,
            "category":      category,
            "subtype":       subtype,
            "rarity":        rarity,
            "level":         level,
            "image_url":     image_url,
            "wiki_url":      wiki_url,
            "obtain":        obtain,
            "dmg_clean":     dmg_clean,
            "dmg_max":       dmg_max,
            "def_clean":     def_clean,
            "def_max":       def_max,
            "upgradeable":   upgradeable,
            "crit":          crit,
            "health_regen":  health_regen,
            "stamina_regen": stamina_regen,
            "price_clean_oml": "",
            "price_max_oml":   "",
            "price_source":    "",
            "price_category":  "",
            "last_updated":  now,
            "updated_at":    wiki_timestamp,
        })

    logger.info(f"Total items procesados: {len(items)}")
    return items
