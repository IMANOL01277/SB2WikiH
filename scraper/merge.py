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
    "category",
    "subtype",
    "rarity",
    "level",
    "image_url",
    "wiki_url",
    "obtain",
    "dmg_clean",
    "dmg_max",
    "def_clean",
    "def_max",
    "upgradeable",
    "crit",
    "health_regen",
    "stamina_regen",
    "price_clean_oml",
    "price_max_oml",
    "price_source",
    "price_category",
    "last_updated",
    "updated_at",
]

def _normalize_name(name: str) -> str:
    """Normaliza nombre para comparacion."""
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def _load_existing_csv(csv_path: str) -> dict:
    if not os.path.exists(csv_path):
        return {}
        
    existing = {}
    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                if name:
                    existing[_normalize_name(name)] = row
    except Exception as exc:
        logger.warning(f"Error cargando CSV existente (se ignorara): {exc}")
        
    return existing


def merge_and_save(wiki_items: list[dict], price_items: dict, csv_path: str):
    existing = _load_existing_csv(csv_path)
    
    final_items = []
    seen = set()
    price_assigned_count = 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    for item in wiki_items:
        name_lower = _normalize_name(item["name"])
        seen.add(name_lower)
        
        # Inject prices
        if name_lower in price_items:
            p_data = price_items[name_lower]
            item["price_clean_oml"] = p_data.get("clean", "")
            item["price_max_oml"]   = p_data.get("max", "")
            item["price_source"]    = p_data.get("source", "")
            item["price_category"]  = p_data.get("category", "")
            price_assigned_count += 1
            
        final_items.append(item)
        
    # Preserve items from old CSV that weren't in the new Wiki scrape
    for name_lower, row in existing.items():
        if name_lower not in seen:
            # Map old columns to new schema if necessary
            # Old schema had type/sub_type/image_link/wiki_link
            legacy_item = {col: "" for col in CSV_COLUMNS}
            
            for col in CSV_COLUMNS:
                if col in row:
                    legacy_item[col] = row[col]
                    
            # Handle renames for legacy items
            if not legacy_item["category"] and "type" in row:
                legacy_item["category"] = row["type"]
            if not legacy_item["subtype"] and "sub_type" in row:
                legacy_item["subtype"] = row["sub_type"]
            if not legacy_item["image_url"] and "image_link" in row:
                legacy_item["image_url"] = row["image_link"]
            if not legacy_item["wiki_url"] and "wiki_link" in row:
                legacy_item["wiki_url"] = row["wiki_link"]
                
            legacy_item["last_updated"] = row.get("last_updated", now)
            
            # Check if it has a price update
            if name_lower in price_items:
                p_data = price_items[name_lower]
                legacy_item["price_clean_oml"] = p_data.get("clean", "")
                legacy_item["price_max_oml"]   = p_data.get("max", "")
                legacy_item["price_source"]    = p_data.get("source", "")
                legacy_item["price_category"]  = p_data.get("category", "")
                price_assigned_count += 1
                
            final_items.append(legacy_item)
            
    # Re-assign IDs based on final order
    for idx, item in enumerate(final_items, start=1):
        item["id"] = idx
        
    # Write to CSV
    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(final_items)
            
        logger.info(f"Precios asignados: {price_assigned_count}/{len(final_items)}")
        
        sin_precio = [i["name"] for i in final_items if not i.get("price_clean_oml")]
        if sin_precio:
            sample = ", ".join(sin_precio[:20])
            extra = f"... y {len(sin_precio)-20} mas" if len(sin_precio) > 20 else ""
            logger.info(f"Sin precio ({len(sin_precio)} items): {sample}{extra}")
            
        logger.info(f"Cambio detectado: {len(existing)} -> {len(final_items)} items")
        logger.info(f"CSV escrito: {csv_path} ({len(final_items)} items, {price_assigned_count} con precio)")
    except Exception as exc:
        logger.error(f"Error guardando CSV {csv_path}: {exc}", exc_info=True)
