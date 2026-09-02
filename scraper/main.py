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

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sb2itemdb")

# Ruta del CSV (relativo al root del proyecto)
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SB2ItemDB.csv")


def main() -> int:
    """
    Pipeline principal:
    1. Scrape wiki -> items
    2. Fetch precios del sheet -> prices
    3. Merge y escribir CSV

    Retorna exit code: 0 = exito, 1 = error critico
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("SB2ItemDB Update Pipeline iniciado")
    logger.info(f"CSV destino: {CSV_PATH}")
    logger.info("=" * 60)

    # --- Paso 1: Scrape del wiki ---
    logger.info("\n[1/3] Scrapeando Item Database del fandom wiki...")
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

    # --- Paso 2: Enriquecer con datos de paginas individuales (Clean/Max damage) ---
    logger.info("\n[2/4] Enriqueciendo items con Clean/Max damage de paginas individuales...")
    try:
        from scraper.item_page_scraper import enrich_items
        wiki_items = enrich_items(wiki_items)
    except Exception as exc:
        logger.error(f"Error en enriquecimiento individual: {exc}", exc_info=True)
        logger.warning("Continuando sin datos de Clean/Max por pagina individual")

    # --- Paso 3: Fetch precios ---
    logger.info("\n[3/4] Descargando precios del Google Sheets...")
    try:
        from scraper.price_scraper import fetch_all_prices
        prices = fetch_all_prices()
    except Exception as exc:
        logger.error(f"Error en price scraper: {exc}", exc_info=True)
        # No abortar: continuar sin precios
        prices = {}
        logger.warning("Continuando sin precios del mercado")

    logger.info(f"Items con precio encontrados: {len(prices)}")

    # --- Paso 4: Merge y escribir CSV ---
    logger.info("\n[4/4] Generando SB2ItemDB.csv...")
    try:
        from scraper.merge import build_csv
        total, with_prices, changed = build_csv(wiki_items, prices, CSV_PATH)
    except Exception as exc:
        logger.error(f"Error critico en merge/escritura: {exc}", exc_info=True)
        return 1

    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline completado exitosamente")
    logger.info(f"  Total items:       {total}")
    logger.info(f"  Items con precio:  {with_prices}")
    logger.info(f"  Cambios detectados: {'SI' if changed else 'NO'}")
    logger.info(f"  Tiempo total:      {elapsed:.1f}s")
    logger.info("=" * 60)

    # Exit code 0 siempre en exito (GitHub Actions commit solo si cambia el archivo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
