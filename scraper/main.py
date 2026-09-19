"""
main.py
~~~~~~~
Orquestador principal del pipeline SB2ItemDB.
Uso: python -m scraper.main
     python scraper/main.py
"""

import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sb2itemdb")

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SB2ItemDB.csv")

def main() -> int:
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("SB2ItemDB Update Pipeline (API Version) iniciado")
    logger.info(f"CSV destino: {CSV_PATH}")
    logger.info("=" * 60)

    # --- Paso 1: Scrape API ---
    logger.info("\n[1/3] Descargando JSON del Item Database (API)...")
    try:
        from scraper.wiki_scraper import scrape_item_database
        wiki_items = scrape_item_database()
    except Exception as exc:
        logger.error(f"Error critico en wiki scraper: {exc}", exc_info=True)
        return 1

    if not wiki_items:
        logger.error("El wiki scraper no retorno items. Abortando.")
        return 1

    logger.info(f"Items obtenidos del wiki: {len(wiki_items)}")

    # --- Paso 2: Fetch precios ---
    logger.info("\n[2/3] Descargando precios del Google Sheets...")
    try:
        from scraper.price_scraper import fetch_all_prices
        prices = fetch_all_prices()
    except Exception as exc:
        logger.error(f"Error en price scraper: {exc}", exc_info=True)
        prices = {}
        logger.warning("Continuando sin precios del mercado")

    logger.info(f"Items con precio encontrados: {len(prices)}")

    # --- Paso 3: Merge y escribir CSV ---
    logger.info("\n[3/3] Generando SB2ItemDB.csv...")
    try:
        from scraper.merge import merge_and_save
        merge_and_save(wiki_items, prices, CSV_PATH)
    except Exception as exc:
        logger.error(f"Error critico en merge/escritura: {exc}", exc_info=True)
        return 1

    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline completado exitosamente")
    logger.info(f"  Tiempo total:      {elapsed:.1f}s")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
