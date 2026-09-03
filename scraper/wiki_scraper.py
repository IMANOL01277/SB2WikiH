"""
wiki_scraper.py
~~~~~~~~~~~~~~~
Scraper del Item Database del fandom de SwordBurst 2.
Extrae todos los items de todas las categorias y retorna una lista de dicts.
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

BASE_URL = "https://swordburst2.fandom.com"
ITEM_DB_URL = f"{BASE_URL}/wiki/Item_Database"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Mapeo de seccion del wiki a tipo canonico
SECTION_TYPE_MAP = {
    "longswords":  ("Longsword",  "Weapon"),
    "greatswords": ("Greatsword", "Weapon"),
    "katanas":     ("Katana",     "Weapon"),
    "rapiers":     ("Rapier",     "Weapon"),
    "spears":      ("Spear",      "Weapon"),
    "scythes":     ("Scythe",     "Weapon"),
    "armors":      ("Armor",      "Armor"),
    "accessories": ("Accessory",  "Accessory"),
    "droppedvelboughtaccessories": ("Accessory", "Accessory"),
    "companions":  ("Companion",  "Companion"),
}

# Criticos por tipo de arma (default del juego)
DEFAULT_CRIT = {
    "Longsword":  "12%",
    "Greatsword": "18%",
    "Katana":     "15%",
    "Rapier":     "11%",
    "Spear":      "21%",
    "Scythe":     "18%",
}



def _fetch_page(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Descarga y parsea una pagina HTML usando la API de MediaWiki."""
    page_title = url.split("/wiki/")[-1]
    api_url = f"https://swordburst2.fandom.com/api.php?action=parse&page={page_title}&format=json"
    
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(api_url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.error(f"Error de API: {data['error']}")
                return None
            html_content = data["parse"]["text"]["*"]
            # Envolvemos el contenido en etiquetas HTML para simular la página completa
            return BeautifulSoup(f"<html><body>{html_content}</body></html>", "lxml")
        except Exception as exc:
            logger.warning(f"Intento {attempt} fallido ({url}): {exc}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    logger.error(f"No se pudo descargar: {url}")
    return None


def _fetch_item_max_stats(item_name: str, wiki_link: str) -> tuple[str, str, str, str]:
    """
    Visita la pagina individual del item para extraer dmg_clean, dmg_max,
    def_clean, def_max desde el infobox de la wiki.
    Retorna (dmg_clean, dmg_max, def_clean, def_max).
    """
    page_title = wiki_link.split("/wiki/")[-1] if wiki_link else item_name.replace(" ", "_")
    api_url = f"https://swordburst2.fandom.com/api.php?action=parse&page={page_title}&format=json"
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        data = resp.json()
        if "error" in data:
            return "", "", "", ""
        soup = BeautifulSoup(data["parse"]["text"]["*"], "lxml")

        dmg_clean, dmg_max = "", ""
        def_clean, def_max = "", ""

        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            is_weapon_table = "base damage" in headers
            is_armor_table = "defense" in headers or "defence" in headers

            if is_weapon_table or is_armor_table:
                for row in table.find_all("tr"):
                    for cell in row.find_all("td"):
                        src = cell.get("data-source", "")
                        if src not in ("dmg", "def"):
                            continue
                        full = cell.get_text(" ", strip=True)
                        m = re.search(
                            r"clean[:\s]+([\d,.]+).*?max[:\s]+([\d,.]+)",
                            full, re.IGNORECASE | re.DOTALL
                        )
                        if m:
                            clean_val = m.group(1).replace(",", "")
                            max_val = m.group(2).replace(",", "")
                        else:
                            clean_val = re.sub(r"[^\d.,]", "", full)
                            max_val = ""

                        if src == "dmg":
                            dmg_clean, dmg_max = clean_val, max_val
                        elif src == "def":
                            def_clean, def_max = clean_val, max_val

        return dmg_clean, dmg_max, def_clean, def_max
    except Exception:
        return "", "", "", ""


def _enrich_items_with_max_stats(items: list[dict], max_workers: int = 20) -> list[dict]:
    """
    Enriquece la lista de items con dmg_clean, dmg_max, def_clean, def_max
    obtenidos concurrentemente desde las paginas individuales del wiki.
    Solo procesa items que sean armas o armaduras (con wiki_link).
    """
    # Filtrar items que necesitan enriquecimiento
    to_enrich = [
        item for item in items
        if item.get("category") in ("Weapon", "Armor") and item.get("wiki_link")
    ]
    logger.info(f"Enriqueciendo {len(to_enrich)} items (dmg/def clean+max) con {max_workers} workers...")

    name_to_stats: dict[str, tuple] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(_fetch_item_max_stats, item["name"], item["wiki_link"]): item["name"]
            for item in to_enrich
        }
        for future in as_completed(future_map):
            name = future_map[future]
            try:
                name_to_stats[name] = future.result()
            except Exception:
                name_to_stats[name] = ("", "", "", "")

    # Aplicar stats enriquecidos
    for item in items:
        if item["name"] in name_to_stats:
            dc, dm, dfc, dfm = name_to_stats[item["name"]]
            if dc:
                item["dmg_clean"] = dc
            if dm:
                item["dmg_max"] = dm
            if dfc:
                item["def_clean"] = dfc
            if dfm:
                item["def_max"] = dfm

    logger.info("Enriquecimiento completado.")
    return items


def _get_image_url(img_tag) -> str:
    """Extrae la URL real de la imagen (soporta lazy-load de Fandom)."""
    if not img_tag:
        return ""
    # Fandom usa data-src para lazy loading
    src = (
        img_tag.get("data-src")
        or img_tag.get("src")
        or ""
    )
    # Limpiar parametros de resize y quedarse con la URL base hasta /revision/latest
    if "wikia.nocookie.net" in src or "static.wikia" in src:
        # Remover parametros de escala para obtener imagen completa
        base = src.split("/scale-to-width")[0].split("/smart/")[0].split("/top-crop")[0]
        if "/revision/latest" not in base:
            base = src  # usar tal cual si no tiene el patron
        return base
    return src


def _clean_text(text: str) -> str:
    """Limpia texto de espacios extra y caracteres de control."""
    return re.sub(r"\s+", " ", text).strip()

def _get_cell_text(cells, index: int) -> str:
    """Obtiene el texto limpio de una celda si el indice es valido."""
    if index >= 0 and index < len(cells):
        return _clean_text(cells[index].get_text())
    return ""

def _parse_item_common(cells, headers_map: dict) -> tuple:
    """Extrae datos comunes (imagen, nombre, link, nivel, rareza, obtain)."""
    # Name and Image are usually in the same cell, denoted by 'name' or index 0 if not found
    name_idx = headers_map.get("name", 0)
    if name_idx >= len(cells):
        return None, "", "", "", "", "", ""
        
    name_cell = cells[name_idx]
    
    img_tag = name_cell.find("img")
    image_url = _get_image_url(img_tag)

    name_link = name_cell.find("a", string=True) # string=True to ignore image links
    if name_link:
        name = _clean_text(name_link.get_text())
        wiki_link = urljoin(BASE_URL, name_link.get("href", ""))
    else:
        # fallback to get all text not in tags or just general text
        text = name_cell.get_text()
        name = _clean_text(text)
        wiki_link = ""

    if not name or name.lower() in ("name", "", "pros:", "cons:"):
        return None, "", "", "", "", "", ""
        
    if len(name) > 50:
        return None, "", "", "", "", "", ""

    level_idx = headers_map.get("lv.", headers_map.get("level", headers_map.get("floor", -1)))
    level_text = _get_cell_text(cells, level_idx)
    level = _extract_level(level_text)

    rarity_idx = headers_map.get("rarity", -1)
    rarity_text = _get_cell_text(cells, rarity_idx)
    rarity = _normalize_rarity(rarity_text)
    
    obtain_idx = headers_map.get("cost/drop", headers_map.get("obtain", headers_map.get("dropped by", -1)))
    obtain = _get_cell_text(cells, obtain_idx)

    return name_cell, name, wiki_link, image_url, level, rarity_text, rarity, obtain


def _parse_weapon_row(cells, headers_map: dict, item_type: str) -> dict | None:
    res = _parse_item_common(cells, headers_map)
    if not res[0]:
        return None
    _, name, wiki_link, image_url, level, rarity_text, rarity, obtain = res

    # Base DMG
    base_dmg_idx = headers_map.get("damage", headers_map.get("base damage", headers_map.get("base dmg", -1)))
    base_dmg = _get_cell_text(cells, base_dmg_idx)
    
    # Crit
    crit_idx = headers_map.get("crit", headers_map.get("critical", -1))
    crit = _get_cell_text(cells, crit_idx) or DEFAULT_CRIT.get(item_type, "")

    # Max DMG - sometimes +20 or +15 or max damage
    max_dmg = ""
    for h in ["+25", "+20", "+15", "+10", "max damage", "max dmg"]:
        if h in headers_map:
            max_dmg = _get_cell_text(cells, headers_map[h])
            break

    return {
        "name":           name,
        "type":           item_type,
        "sub_type":       _detect_sub_type(name, rarity_text),
        "category":       "Weapon",
        "rarity":         rarity,
        "level":          level,
        "dmg_clean":       base_dmg,
        "dmg_max":        max_dmg,
        "def_clean":       "",
        "def_max":        "",
        "upgradeable":    _is_upgradeable(rarity),
        "crit":           crit,
        "health_regen":   "",
        "stamina_regen":  "",
        "obtain":         obtain,
        "image_link":     image_url,
        "wiki_link":      wiki_link,
    }


def _parse_armor_row(cells, headers_map: dict) -> dict | None:
    res = _parse_item_common(cells, headers_map)
    if not res[0]:
        return None
    _, name, wiki_link, image_url, level, rarity_text, rarity, obtain = res

    base_def = _get_cell_text(cells, headers_map.get("defense", headers_map.get("base defense", headers_map.get("base def", -1))))
    
    max_def = ""
    for h in ["+25", "+20", "+15", "+10", "max defense", "max def"]:
        if h in headers_map:
            max_def = _get_cell_text(cells, headers_map[h])
            break

    return {
        "name":           name,
        "type":           "Armor",
        "sub_type":       _detect_sub_type(name, rarity_text),
        "category":       "Armor",
        "rarity":         rarity,
        "level":          level,
        "dmg_clean":       "",
        "dmg_max":        "",
        "def_clean":       base_def,
        "def_max":        max_def,
        "upgradeable":    _is_upgradeable(rarity),
        "crit":           "",
        "health_regen":   "",
        "stamina_regen":  "",
        "obtain":         obtain,
        "image_link":     image_url,
        "wiki_link":      wiki_link,
    }


def _parse_accessory_row(cells, headers_map: dict) -> dict | None:
    res = _parse_item_common(cells, headers_map)
    if not res[0]:
        return None
    _, name, wiki_link, image_url, level, rarity_text, rarity, obtain = res

    # En accesorios los stats pueden estar en una sola columna "stats" o separados
    health_regen = ""
    stamina_regen = ""
    
    # Check if there is a 'stats' column
    stats_idx = headers_map.get("stats", -1)
    if stats_idx >= 0:
        txt = _get_cell_text(cells, stats_idx)
        if "health" in txt.lower() or "hp" in txt.lower():
            m = re.search(r"(\d+\.?\d*%?)", txt[txt.lower().find("h"):])
            if m: health_regen = m.group(1)
        if "stamina" in txt.lower() or "stam" in txt.lower():
            m = re.search(r"(\d+\.?\d*%?)", txt[txt.lower().find("s"):])
            if m: stamina_regen = m.group(1)

    return {
        "name":           name,
        "type":           "Accessory",
        "sub_type":       "",
        "category":       "Accessory",
        "rarity":         rarity,
        "level":          level,
        "dmg_clean":       "",
        "dmg_max":        "",
        "def_clean":       "",
        "def_max":        "",
        "upgradeable":    "FALSE",
        "crit":           "",
        "health_regen":   health_regen,
        "stamina_regen":  stamina_regen,
        "obtain":         obtain,
        "image_link":     image_url,
        "wiki_link":      wiki_link,
    }


def _parse_companion_row(cells, headers_map: dict) -> dict | None:
    res = _parse_item_common(cells, headers_map)
    if not res[0]:
        return None
    _, name, wiki_link, image_url, level, rarity_text, rarity, obtain = res

    return {
        "name":           name,
        "type":           "Companion",
        "sub_type":       "",
        "category":       "Companion",
        "rarity":         rarity,
        "level":          "",
        "dmg_clean":       "",
        "dmg_max":        "",
        "def_clean":       "",
        "def_max":        "",
        "upgradeable":    "FALSE",
        "crit":           "",
        "health_regen":   "",
        "stamina_regen":  "",
        "obtain":         obtain,
        "image_link":     image_url,
        "wiki_link":      wiki_link,
    }


def _extract_level(text: str) -> str:
    """Extrae el numero de nivel de textos como 'Floor 5', '50', '1-5'."""
    if not text:
        return ""
    # Numero directo
    if re.match(r"^-?\d+$", text):
        return text
    # Floor N
    m = re.search(r"floor\s*(\d+)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    # Nivel con operacion: "3+lvl"
    if "lvl" in text.lower() or "+" in text:
        return text
    # Primer numero encontrado
    m = re.search(r"(\d+)", text)
    if m:
        return m.group(1)
    return text


def _normalize_rarity(rarity_text: str) -> str:
    """Normaliza el texto de rareza a un valor canonico."""
    mapping = {
        "common":    "Common",
        "uncommon":  "Uncommon",
        "rare":      "Rare",
        "legendary": "Legendary",
        "tribute":   "Tribute",
        "burst":     "Burst",
        "limited":   "Legendary",
    }
    rt = rarity_text.lower().strip()
    for key, val in mapping.items():
        if key in rt:
            return val
    return rarity_text.title() if rarity_text else ""


def _is_upgradeable(rarity: str) -> str:
    """Determina si el item es upgradeable segun su rareza."""
    non_upgradeable = {"tribute", "burst"}
    if rarity.lower() in non_upgradeable:
        return "FALSE"
    return "TRUE"


def _detect_sub_type(name: str, rarity_text: str) -> str:
    """Detecta el sub_type basado en el nombre o texto de rareza."""
    nl = name.lower()
    rl = rarity_text.lower()
    if "limited" in rl or "limited" in nl:
        return "Limited"
    if "forgotten" in nl:
        return f"Forgotten {name.split()[0] if name.split() else ''}"
    return ""


def _parse_table_for_section(section_key: str, table, item_type: str, category: str) -> list[dict]:
    """Parsea una tabla wikitable y retorna lista de items."""
    items = []
    
    # Extraer headers de la tabla para saber en que columna esta cada dato
    headers = [th.get_text().strip().lower() for th in table.find_all("th")]
    headers_map = {h: i for i, h in enumerate(headers) if h}
    
    rows = table.find_all("tr")

    data_rows = []
    for row in rows:
        if row.find("th"):
            continue
        cells = row.find_all("td")
        if cells:
            data_rows.append(cells)

    for cells in data_rows:
        try:
            if category == "Weapon":
                item = _parse_weapon_row(cells, headers_map, item_type)
            elif category == "Armor":
                item = _parse_armor_row(cells, headers_map)
            elif category == "Accessory":
                item = _parse_accessory_row(cells, headers_map)
            elif category == "Companion":
                item = _parse_companion_row(cells, headers_map)
            else:
                item = None

            if item and item.get("name"):
                items.append(item)
        except Exception as exc:
            logger.debug(f"Error parseando fila en {section_key}: {exc}")

    return items


def scrape_item_database() -> list[dict]:
    """
    Funcion principal: scrape completo del Item Database.
    Retorna lista de dicts con todos los items.
    """
    logger.info(f"Descargando Item Database: {ITEM_DB_URL}")
    soup = _fetch_page(ITEM_DB_URL)
    if not soup:
        logger.error("No se pudo obtener la pagina del Item Database")
        return []

    all_items = []
    seen_names = set()

    for table in soup.find_all("table"):
        # Buscar el encabezado principal h2 mas cercano hacia atras
        h2 = table.find_previous("h2")
        if not h2:
            continue
        
        heading_text = _clean_text(h2.get_text()).lower()
        heading_text = re.sub(r"\[.*?\]", "", heading_text).strip()
        heading_key = re.sub(r"[^a-z]", "", heading_text)

        if heading_key in SECTION_TYPE_MAP:
            current_type, current_category = SECTION_TYPE_MAP[heading_key]
            
            section_items = _parse_table_for_section(
                heading_key, table, current_type, current_category
            )
            for item in section_items:
                name_lower = item["name"].lower()
                if name_lower not in seen_names:
                    seen_names.add(name_lower)
                    all_items.append(item)
                else:
                    logger.debug(f"Item duplicado ignorado: {item['name']}")

    # ====== NUEVO BLOQUE: EXTRAER AURAS ======
    try:
        logger.info("Descargando Auras: https://swordburst2.fandom.com/wiki/Auras")
        soup_auras = _fetch_page("https://swordburst2.fandom.com/wiki/Auras")
        if not soup_auras:
            raise ValueError("No se pudo obtener la página de Auras")
        
        auras_found = 0
        for i, table in enumerate(soup_auras.find_all("table")):
            if i == 0: continue
            rows = table.find_all("tr")
            if len(rows) < 2: continue
            
            name_row, image_row, rarity_row = None, None, None
            for idx, row in enumerate(rows):
                style = row.get("style", "")
                if "font-weight: bold" in style or "font-weight:bold" in style:
                    name_row = row
                    if idx > 0: image_row = rows[idx-1]
                    if idx + 1 < len(rows): rarity_row = rows[idx+1]
                    break
                    
            if not name_row and len(rows) >= 3:
                image_row, name_row, rarity_row = rows[0], rows[1], rows[2]
                
            if not name_row: continue
                
            name_cells = name_row.find_all(["td", "th"])
            img_cells = image_row.find_all(["td", "th"]) if image_row else []
            rarity_cells = rarity_row.find_all(["td", "th"]) if rarity_row else []
            
            for j, cell in enumerate(name_cells):
                name = cell.get_text(separator=" ").strip()
                if not name or "Aura Chest" in name: continue
                
                rarity = ""
                if rarity_row and j < len(rarity_cells):
                    rarity = rarity_cells[j].get_text(separator=" ").strip()
                    
                rarity_clean = re.sub(r"Drop.*", "", rarity, flags=re.IGNORECASE).strip()
                if not rarity_clean and j < len(rarity_cells):
                    for d in rarity_cells[j].find_all("div"):
                        t = d.get_text(separator=" ").strip()
                        if t in ["Common", "Uncommon", "Rare", "Legendary"]:
                            rarity_clean = t
                            break
                rarity = rarity_clean if rarity_clean else "Legendary"
                
                img_url = ""
                img_idx = j + 1 if len(img_cells) > len(name_cells) else j
                if image_row and img_idx < len(img_cells):
                    img_tag = img_cells[img_idx].find("img")
                    if img_tag:
                        img_url = img_tag.get("data-src") or img_tag.get("src") or ""
                        img_url = img_url.split("/revision")[0] if "/revision" in img_url else img_url
                        if img_url.startswith("data:image"): img_url = ""
                        
                wiki_name = name.replace(" ", "_")
                all_items.append({
                    "name": name,
                    "type": "Aura",
                    "sub_type": "Aura",
                    "category": "Aura",
                    "rarity": rarity,
                    "level": "",
                    "dmg_clean": "",
                    "dmg_max": "",
                    "def_clean": "",
                    "def_max": "",
                    "upgradeable": "FALSE",
                    "crit": "",
                    "health_regen": "",
                    "stamina_regen": "",
                    "obtain": "",
                    "image_link": img_url,
                    "wiki_link": f"https://swordburst2.fandom.com/wiki/{wiki_name}"
                })
                auras_found += 1
                
        logger.info(f"Total auras scrapeadas: {auras_found}")
    except Exception as exc:
        logger.error(f"Error parseando Auras: {exc}", exc_info=True)
    # ==========================================

    logger.info(f"Total items scrapeados del wiki: {len(all_items)}")

    # [2/2] Enriquecer con dmg_max, def_clean y def_max desde paginas individuales
    all_items = _enrich_items_with_max_stats(all_items, max_workers=20)

    return all_items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    items = scrape_item_database()
    print(f"\nTotal items: {len(items)}")
    for item in items[:5]:
        print(item)
