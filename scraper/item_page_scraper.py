"""
item_page_scraper.py
~~~~~~~~~~~~~~~~~~~~~
Visita las paginas individuales de cada item en el wiki de SB2
para extraer el Clean y Max damage/defense y demas stats completos.
Usa threading para hacerlo rapido en paralelo.
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://swordburst2.fandom.com"
MAX_WORKERS = 8   # Peticiones en paralelo (no demasiadas para no ser baneados)
DELAY = 0.3       # Segundos entre lotes


def _make_scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )


def _parse_clean_max(text: str):
    """
    Extrae clean y max de textos como:
      'Clean: 419Max: 838'
      'Clean: 419\nMax: 838'
      '419'  (sin upgrade -> clean=419, max='')
    """
    text = re.sub(r"\s+", " ", text).strip()
    clean, max_ = "", ""

    m_clean = re.search(r"[Cc]lean[:\s]+([0-9,\.]+)", text)
    m_max   = re.search(r"[Mm]ax[:\s]+([0-9,\.]+)", text)

    if m_clean:
        clean = m_clean.group(1).replace(",", "")
    if m_max:
        max_ = m_max.group(1).replace(",", "")

    # Si no tiene "Clean/Max" es un valor unico (upgradeable no especificado)
    if not clean and not max_:
        m_single = re.search(r"([0-9,]+)", text)
        if m_single:
            clean = m_single.group(1).replace(",", "")

    return clean, max_


def scrape_item_page(wiki_link: str, scraper=None) -> dict:
    """
    Visita la pagina individual del item y extrae:
    - base_dmg_clean, base_dmg_max  (o base_def_clean, base_def_max para armaduras)
    - crit, level, health_regen, stamina_regen, obtain
    Retorna un dict vacio si no se puede parsear.
    """
    if not wiki_link or "fandom.com" not in wiki_link:
        return {}

    if scraper is None:
        scraper = _make_scraper()

    try:
        resp = scraper.get(wiki_link, timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        logger.debug(f"Error descargando {wiki_link}: {exc}")
        return {}

    soup = BeautifulSoup(resp.text, "lxml")
    result = {}

    for table in soup.find_all("table"):
        headers_raw = [th.get_text().strip() for th in table.find_all("th")]
        headers = [h.lower() for h in headers_raw]

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            row_data = [c.get_text(separator=" ").strip() for c in cells]

            # Tabla con Level / Base Damage / Crit (armas)
            if "base damage" in headers:
                h = headers
                if "level" in h and len(row_data) > h.index("level"):
                    result["level"] = row_data[h.index("level")]
                if "base damage" in h and len(row_data) > h.index("base damage"):
                    raw_dmg = row_data[h.index("base damage")]
                    raw_lower = raw_dmg.lower()

                    # Detectar arma level-scaling (dmg aumenta por nivel, no upgradeable)
                    if "per level" in raw_lower or "based on level" in raw_lower or "level based" in raw_lower:
                        result["level_scaling"] = True
                        result["upgradeable"] = "FALSE"
                        # Guardar la formula de escalado como dmg_clean (ej: "+145 per level")
                        formula = re.sub(r"\s+", " ", raw_dmg).strip()
                        result["base_dmg_clean"] = formula
                        result["base_dmg_max"]   = ""
                    else:
                        result["level_scaling"] = False
                        clean, max_ = _parse_clean_max(raw_dmg)
                        result["base_dmg_clean"] = clean
                        result["base_dmg_max"]   = max_

                if "crit" in h and len(row_data) > h.index("crit"):
                    result["crit"] = row_data[h.index("crit")]

            # Tabla con Defense (armaduras)
            if "base defense" in headers or "defense" in headers:
                h = headers
                def_key = "base defense" if "base defense" in h else "defense"
                if def_key in h and len(row_data) > h.index(def_key):
                    clean, max_ = _parse_clean_max(row_data[h.index(def_key)])
                    result["base_def_clean"] = clean
                    result["base_def_max"]   = max_

            # Tabla con Abilities / Obtain (stats adicionales)
            if "abilities" in headers or "obtain" in headers:
                h = headers
                if "abilities" in h and len(row_data) > h.index("abilities"):
                    abilities_txt = row_data[h.index("abilities")]
                    m_hp  = re.search(r"(\d+\.?\d*)%?\s*Health Reg", abilities_txt, re.I)
                    m_stm = re.search(r"(\d+\.?\d*)%?\s*Stamina Reg", abilities_txt, re.I)
                    if m_hp:  result["health_regen"]  = m_hp.group(1) + "%"
                    if m_stm: result["stamina_regen"] = m_stm.group(1) + "%"
                if "obtain" in h and len(row_data) > h.index("obtain"):
                    result["obtain"] = row_data[h.index("obtain")]

    return result


def enrich_items(items: list) -> list:
    """
    Visita en paralelo las paginas individuales de cada item
    y enriquece los datos con Clean/Max damage.
    Retorna la lista de items enriquecidos.
    """
    logger.info(f"Enriqueciendo {len(items)} items con datos de paginas individuales...")

    # Solo enriquecer items que tienen wiki_link
    to_enrich = [(i, item) for i, item in enumerate(items) if item.get("wiki_link")]
    logger.info(f"Items con wiki_link: {len(to_enrich)}")

    results_map = {}  # index -> extra_data

    scraper = _make_scraper()

    def fetch_one(idx_item):
        idx, item = idx_item
        extra = scrape_item_page(item["wiki_link"], scraper)
        return idx, extra

    # Procesar en lotes con ThreadPoolExecutor
    batch_size = MAX_WORKERS
    total = len(to_enrich)
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_one, pair): pair for pair in to_enrich}
        for future in as_completed(futures):
            try:
                idx, extra = future.result(timeout=30)
                if extra:
                    results_map[idx] = extra
                done += 1
                if done % 50 == 0:
                    logger.info(f"  Progreso: {done}/{total} items procesados...")
                    time.sleep(DELAY)
            except Exception as exc:
                logger.debug(f"Error en future: {exc}")

    logger.info(f"Paginas individuales procesadas: {done}/{total}")

    # Aplicar los datos extras a cada item
    enriched_count = 0
    for i, item in enumerate(items):
        extra = results_map.get(i, {})
        if not extra:
            continue

        enriched_count += 1
        category = item.get("category", "")

        # Sobrescribir con datos de la pagina individual (mas precisos)
        if extra.get("level"):
            item["level"] = extra["level"]
        
        if extra.get("upgradeable"):
            item["upgradeable"] = extra["upgradeable"]

        if category == "Weapon":
            if extra.get("base_dmg_clean"):
                item["dmg_clean"] = extra["base_dmg_clean"]
            if extra.get("base_dmg_max"):
                item["dmg_max"] = extra["base_dmg_max"]
            if extra.get("crit"):
                item["crit"] = extra["crit"]
        elif category == "Armor":
            if extra.get("base_def_clean"):
                item["def_clean"] = extra["base_def_clean"]
            if extra.get("base_def_max"):
                item["def_max"] = extra["base_def_max"]

        # Stats adicionales (todos los tipos)
        if extra.get("health_regen"):
            item["health_regen"] = extra["health_regen"]
        if extra.get("stamina_regen"):
            item["stamina_regen"] = extra["stamina_regen"]
        if extra.get("obtain") and not item.get("obtain"):
            item["obtain"] = extra["obtain"]

    logger.info(f"Items enriquecidos con datos completos: {enriched_count}/{len(items)}")
    return items


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test rapido con un solo item
    result = scrape_item_page("https://swordburst2.fandom.com/wiki/Desert_Storm")
    print("Desert Storm:", result)
    result2 = scrape_item_page("https://swordburst2.fandom.com/wiki/Ethereal_Edge")
    print("Ethereal Edge:", result2)
