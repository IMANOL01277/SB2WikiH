"""
price_scraper.py
~~~~~~~~~~~~~~~~
Descarga y parsea el Google Sheets de precios del mercado P2P de SwordBurst 2.
Retorna un dict normalizado: { item_name_lower: { clean, max, source, category, raw_name } }
"""

import csv
import io
import logging
import re
import time
from difflib import SequenceMatcher

import requests

logger = logging.getLogger(__name__)

SPREADSHEET_ID = "1EZkeyhJGaWuai37KfjvrMOiVCmjhmf6m0AJ-cvbzCGI"

SHEETS = {
    "tributes":          1446399948,
    "clean_legendaries": 905963426,
    "max_legendaries":   628419816,
    "accessories":       1019617648,
    "misc":              1084564302,
    "auras":             780998096,
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

FUZZY_THRESHOLD = 0.85

# Palabras clave que indican fila de seccion (no son items)
SECTION_KEYWORDS = {
    "floor", "arcadia", "atheon", "realm", "edition", "event", "misc",
    "merchant", "gift", "guild", "rotational", "exclusive", "bundle",
    "normal", "seasonal", "undershroud", "capes", "scarfs", "scarves",
    "head gear", "headgear", "waist", "dragon pal", "bunny pal", "plush",
    "fish pal", "kitsune", "burst store", "item crystal", "main floor",
    "rotational floor", "event floor", "gift tribute",
}

SKIP_KEYWORDS = {
    "1 oml", "value of item", "check out", "updated as of",
    "gmt", "disclaimer", "how to calculate", "blame", "man this",
    "deflating", "inflating", "stable", "demand", "unstable",
    "collector", "rare/not", "ddddd", "wwwww", "rrrrr",
    "history changes", "south east", "timezone",
}


def _normalize(name: str) -> str:
    """Lowercase, strip espacios, quitar caracteres especiales."""
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def _fuzzy_match(query: str, candidates: list) -> str | None:
    """Retorna el candidato mas cercano si supera el umbral."""
    best_score = 0.0
    best_match = None
    q = _normalize(query)
    for c in candidates:
        score = SequenceMatcher(None, q, _normalize(c)).ratio()
        if score > best_score:
            best_score = score
            best_match = c
    if best_score >= FUZZY_THRESHOLD:
        return best_match
    return None


def _fetch_csv(sheet_name: str, gid: int, retries: int = 3) -> list:
    """Descarga un sheet como CSV y lo retorna como lista de filas."""
    url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
        f"/export?format=csv&gid={gid}"
    )
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            text = resp.content.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            logger.info(f"[{sheet_name}] Descargado: {len(rows)} filas")
            return rows
        except Exception as exc:
            logger.warning(f"[{sheet_name}] Intento {attempt} fallido: {exc}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    logger.error(f"[{sheet_name}] No se pudo descargar tras {retries} intentos")
    return []


def _is_price_value(cell: str) -> bool:
    """Retorna True si la celda parece un precio valido."""
    c = cell.strip()
    if not c:
        return False
    cl = c.lower()
    # Untradeable y ? son precios validos
    if cl in ("untradeable", "?", "n/a"):
        return True
    # Numero simple o rango: 5, 5-8, 0.5-1, 3k-3.5k, 15-16k, 3m-5m vels
    patterns = [
        r"^\d+(\.\d+)?$",
        r"^\d+(\.\d+)?\s*-\s*\d+(\.\d+)?$",
        r"^\d+(\.\d+)?[km](\s*-\s*\d+(\.\d+)?[km]?)?(\s*vels?)?$",
        r"^\d+[km]?\s*vels?$",
        r"^\d+[km]?\s*\+$",
    ]
    for p in patterns:
        if re.match(p, cl):
            return True
    # Rango con espacios
    if re.match(r"^[\d\.\-k m\+]+$", cl) and any(ch.isdigit() for ch in cl):
        return True
    return False


def _is_item_name(cell: str) -> bool:
    """Retorna True si la celda parece un nombre de item."""
    c = cell.strip()
    if not c:
        return False
    # Saltar si es puramente numerico
    if re.match(r"^[\d\.\-\s]+$", c):
        return False
    # Saltar celdas de metadata
    skip = {"n", "r", "ddddd", "wwwww", "rrrrr", "clean", "max"}
    if c.lower() in skip:
        return False
    # Saltar palabras clave de seccion
    cl = c.lower()
    if any(kw in cl for kw in SKIP_KEYWORDS):
        return False
    return True


def _is_section_row(cells: list) -> str | None:
    """
    Detecta si una fila es una fila de seccion/categoria.
    Retorna el nombre de categoria o None.
    """
    non_empty = [c.strip() for c in cells if c.strip()]
    if not non_empty:
        return None

    first = non_empty[0].lower()

    # Verificar si alguna celda inicial contiene keyword de seccion
    for cell in non_empty[:5]:
        cl = cell.lower()
        for kw in SECTION_KEYWORDS:
            if kw in cl and len(cell) < 80:
                # Es una fila de seccion, construir nombre
                # Filtrar celdas de metadata
                cat_parts = []
                for nc in non_empty[:4]:
                    if not any(sk in nc.lower() for sk in SKIP_KEYWORDS):
                        cat_parts.append(nc)
                return " ".join(cat_parts).strip() or cell

    # Si el primer elemento es "Clean" o "Max", no es seccion
    if first in ("clean", "max"):
        return None

    return None


def _parse_row_pairs(cells: list, source: str, category: str,
                     condition: str | None, prices: dict) -> None:
    """Extrae pares (precio, nombre) de una fila del spreadsheet."""
    i = 0
    n = len(cells)
    while i < n:
        cell = cells[i].strip()
        if _is_price_value(cell):
            # Buscar el nombre en las siguientes celdas no vacias
            j = i + 1
            while j < n and not cells[j].strip():
                j += 1
            if j < n:
                name_cell = cells[j].strip()
                if _is_item_name(name_cell):
                    _store_price(prices, name_cell, cell, source, category, condition)
                    i = j + 1
                    continue
        i += 1


def _store_price(prices: dict, raw_name: str, price_val: str,
                 source: str, category: str, condition: str | None) -> None:
    """Guarda el precio en el dict."""
    key = _normalize(raw_name)
    if not key or len(key) < 2:
        return

    if key not in prices:
        prices[key] = {
            "raw_name": raw_name,
            "clean":    "",
            "max":      "",
            "source":   source,
            "category": category,
        }

    entry = prices[key]
    pv = price_val.strip()

    if condition == "max":
        if not entry["max"]:
            entry["max"] = pv
    elif condition == "clean":
        if not entry["clean"]:
            entry["clean"] = pv
    else:
        # Sin condicion explicita (accesorios): precio general -> clean
        if not entry["clean"]:
            entry["clean"] = pv

    # Actualizar categoria
    entry["category"] = category


def _parse_price_sheet(rows: list, source: str) -> dict:
    """Parsea el formato irregular del spreadsheet de precios."""
    prices = {}
    current_category = "General"
    current_condition = None  # "clean" o "max"

    for row in rows:
        stripped = [c.strip() for c in row]
        non_empty = [c for c in stripped if c]
        if not non_empty:
            continue

        # Saltar filas de metadata global
        skip_row = False
        for cell in non_empty:
            if any(sk in cell.lower() for sk in SKIP_KEYWORDS):
                skip_row = True
                break
        if skip_row:
            continue

        # Detectar condicion (Clean / Max)
        first = non_empty[0].lower()
        if first == "clean":
            current_condition = "clean"
        elif first == "max":
            current_condition = "max"

        # Detectar seccion
        section_name = _is_section_row(stripped)
        if section_name:
            current_category = section_name
            # Reset condicion al cambiar de seccion (solo para tributes/legendaries)
            if source in ("tributes", "clean_legendaries", "max_legendaries"):
                current_condition = None
            continue

        # Parsear pares precio+nombre
        _parse_row_pairs(stripped, source, current_category, current_condition, prices)

    logger.info(f"[{source}] Items con precio parseados: {len(prices)}")
    return prices


def fetch_all_prices() -> dict:
    """
    Descarga y parsea todos los sheets de precios.
    Retorna dict unificado: { item_name_lower: { clean, max, source, category, raw_name } }
    """
    all_prices = {}

    for sheet_name, gid in SHEETS.items():
        logger.info(f"Descargando sheet: {sheet_name}")
        rows = _fetch_csv(sheet_name, gid)
        if not rows:
            continue

        # Para clean_legendaries y max_legendaries, mergear en vez de separar
        if sheet_name == "max_legendaries":
            sheet_prices = _parse_price_sheet(rows, "max_legendaries")
            for key, data in sheet_prices.items():
                if key in all_prices:
                    # Completar el max del item si ya existe como clean_legendary
                    if not all_prices[key]["max"] and data["clean"]:
                        all_prices[key]["max"] = data["clean"]
                    elif not all_prices[key]["max"] and data["max"]:
                        all_prices[key]["max"] = data["max"]
                else:
                    # Nuevo item, guardarlo pero marcar el precio como max
                    entry = dict(data)
                    if entry["clean"] and not entry["max"]:
                        entry["max"] = entry["clean"]
                        entry["clean"] = ""
                    all_prices[key] = entry
            continue

        sheet_prices = _parse_price_sheet(rows, sheet_name)
        for key, data in sheet_prices.items():
            if key not in all_prices:
                all_prices[key] = data
            else:
                existing = all_prices[key]
                if not existing["clean"] and data["clean"]:
                    existing["clean"] = data["clean"]
                if not existing["max"] and data["max"]:
                    existing["max"] = data["max"]

    logger.info(f"Total items con precio en todos los sheets: {len(all_prices)}")
    return all_prices


def lookup_price(item_name: str, prices: dict) -> dict:
    """Busca el precio de un item. Primero exacto, luego fuzzy."""
    key = _normalize(item_name)
    if key in prices:
        return prices[key]

    # Fuzzy search
    candidate = _fuzzy_match(item_name, [p["raw_name"] for p in prices.values()])
    if candidate:
        candidate_key = _normalize(candidate)
        logger.debug(f"Fuzzy match '{item_name}' -> '{candidate}'")
        return prices.get(candidate_key, {})

    return {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prices = fetch_all_prices()
    test_names = ["Desert Storm", "Sea Splitter", "Crimson Dragon", "Godly Bunny", "Rock", "Frozen Euphoria", "Spirit Blossom"]
    print(f"\nTotal precios: {len(prices)}\n--- Tests ---")
    for name in test_names:
        r = lookup_price(name, prices)
        print(f"  {name}: clean={r.get('clean','?')} max={r.get('max','?')} [{r.get('source','-')}]")
