"""
merge.py
~~~~~~~~
Une los datos del wiki con los precios del sheet P2P y genera SB2ItemDB.csv.
Preserva datos existentes del CSV si el wiki no tiene el item.
"""

import csv
import logging
import os
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "id",
    "name",
    "type",
    "sub_type",
    "category",
    "rarity",
    "level",
    "base_dmg",
    "max_dmg",
    "base_def",
    "max_def",
    "upgradeable",
    "crit",
    "health_regen",
    "stamina_regen",
    "obtain",
    "image_link",
    "wiki_link",
    "price_clean_oml",
    "price_max_oml",
    "price_source",
    "price_category",
    "last_updated",
]


def _normalize_name(name: str) -> str:
    """Normaliza nombre para comparacion."""
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def _load_existing_csv(csv_path: str) -> dict:
    """
    Carga el CSV existente y retorna dict { name_lower: row_dict }.
    Preserva datos de items que no esten en el wiki.
    """
    if not os.path.exists(csv_path):
        return {}

    existing = {}
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                if name:
                    key = _normalize_name(name)
                    existing[key] = row
        logger.info(f"CSV existente cargado: {len(existing)} items")
    except Exception as exc:
        logger.warning(f"No se pudo cargar CSV existente: {exc}")

    return existing


def _merge_with_existing(wiki_item: dict, existing: dict) -> dict:
    """
    Combina datos del wiki con datos existentes del CSV.
    El wiki tiene prioridad para datos de stats; el CSV preserva datos faltantes.
    """
    key = _normalize_name(wiki_item["name"])
    old = existing.get(key, {})

    merged = dict(wiki_item)

    # Si el wiki no tiene imagen pero el CSV si, usar la del CSV
    if not merged.get("image_link") and old.get("image_link"):
        merged["image_link"] = old["image_link"]

    # Si el wiki no tiene wiki_link pero el CSV si
    if not merged.get("wiki_link") and old.get("wiki_link"):
        merged["wiki_link"] = old["wiki_link"]

    # Si el wiki no tiene obtain pero el CSV si
    if not merged.get("obtain") and old.get("obtain"):
        merged["obtain"] = old["obtain"]

    # Preservar sub_type del CSV si el wiki no lo tiene y el CSV tiene uno especifico
    if not merged.get("sub_type") and old.get("sub_type"):
        merged["sub_type"] = old["sub_type"]

    # Preservar precios del CSV si existen y el nuevo scraper no encontro nada
    if not merged.get("price_clean_oml") and old.get("price_clean_oml"):
        merged["price_clean_oml"] = old["price_clean_oml"]
        merged["price_max_oml"] = old.get("price_max_oml", "")
        merged["price_source"] = old.get("price_source", "")
        merged["price_category"] = old.get("price_category", "")

    return merged


def _apply_prices(items: list, prices: dict) -> list:
    """Aplica los precios a cada item usando lookup exacto + fuzzy."""
    from scraper.price_scraper import lookup_price

    matched = 0
    unmatched = []

    for item in items:
        price_data = lookup_price(item["name"], prices)
        if price_data:
            item["price_clean_oml"] = price_data.get("clean", "")
            item["price_max_oml"]   = price_data.get("max", "")
            item["price_source"]    = price_data.get("source", "")
            item["price_category"]  = price_data.get("category", "")
            matched += 1
        else:
            item["price_clean_oml"] = item.get("price_clean_oml", "")
            item["price_max_oml"]   = item.get("price_max_oml", "")
            item["price_source"]    = item.get("price_source", "")
            item["price_category"]  = item.get("price_category", "")
            unmatched.append(item["name"])

    logger.info(f"Precios asignados: {matched}/{len(items)}")
    if unmatched:
        logger.info(f"Sin precio ({len(unmatched)} items): {', '.join(unmatched[:20])}" +
                    (f"... y {len(unmatched)-20} mas" if len(unmatched) > 20 else ""))

    return items


def build_csv(wiki_items: list, prices: dict, csv_path: str) -> tuple:
    """
    Construye el CSV final mezclando wiki items, precios, y datos existentes.
    
    Retorna: (total_items, items_with_prices, changes_detected)
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Cargar CSV existente para preservar datos
    existing = _load_existing_csv(csv_path)
    old_count = len(existing)

    # Merge datos del wiki con existentes
    merged_items = []
    seen_names = set()
    for item in wiki_items:
        key = _normalize_name(item["name"])
        if key in seen_names:
            continue
        seen_names.add(key)
        merged = _merge_with_existing(item, existing)
        merged_items.append(merged)

    # Agregar items del CSV existente que NO esten en el wiki (legacy/manual)
    for key, old_row in existing.items():
        if key not in seen_names:
            logger.debug(f"Item legacy preservado: {old_row.get('name', key)}")
            legacy_item = {col: old_row.get(col, "") for col in CSV_COLUMNS}
            # Asegurar campos nuevos existan
            if "price_clean_oml" not in legacy_item:
                legacy_item["price_clean_oml"] = ""
                legacy_item["price_max_oml"] = ""
                legacy_item["price_source"] = ""
                legacy_item["price_category"] = ""
            merged_items.append(legacy_item)
            seen_names.add(key)

    # Aplicar precios
    merged_items = _apply_prices(merged_items, prices)

    # Agregar timestamp y asignar IDs
    for i, item in enumerate(merged_items, start=1):
        item["id"] = str(i)
        item["last_updated"] = timestamp

    # Detectar cambios respecto al CSV anterior
    changes_detected = False
    new_count = len(merged_items)
    if new_count != old_count:
        changes_detected = True
        logger.info(f"Cambio detectado: {old_count} -> {new_count} items")
    else:
        # Verificar cambios en precios
        for item in merged_items:
            key = _normalize_name(item.get("name", ""))
            old = existing.get(key, {})
            if (item.get("price_clean_oml") != old.get("price_clean_oml") or
                    item.get("price_max_oml") != old.get("price_max_oml")):
                changes_detected = True
                logger.info(f"Precio actualizado: {item.get('name')}")
                break

    # Escribir CSV
    items_with_prices = sum(
        1 for item in merged_items if item.get("price_clean_oml") or item.get("price_max_oml")
    )

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_COLUMNS,
            extrasaction="ignore",
            lineterminator="\r\n",
        )
        writer.writeheader()
        writer.writerows(merged_items)

    logger.info(f"CSV escrito: {csv_path} ({new_count} items, {items_with_prices} con precio)")
    return new_count, items_with_prices, changes_detected


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test rapido
    test_items = [
        {"name": "Desert Storm", "type": "Longsword", "sub_type": "", "category": "Weapon",
         "rarity": "Legendary", "level": "50", "base_dmg": "419", "max_dmg": "838",
         "base_def": "", "max_def": "", "upgradeable": "TRUE", "crit": "12%",
         "health_regen": "3%", "stamina_regen": "2%", "obtain": "Fire Scorpion",
         "image_link": "https://example.com/desert_storm.png",
         "wiki_link": "https://swordburst2.fandom.com/wiki/Desert_Storm"},
    ]
    from scraper.price_scraper import fetch_all_prices
    prices = fetch_all_prices()
    n, p, changed = build_csv(test_items, prices, "SB2ItemDB.csv")
    print(f"Total: {n}, Con precio: {p}, Cambios: {changed}")
