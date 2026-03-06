#!/usr/bin/env python3
"""
Monitor Inmobiliario — GBA Norte
Fuentes: MercadoLibre API (confiable) + Argenprop (HTML corregido)
Zonas: Vicente López, Florida, La Lucila, San Isidro
Precio: USD 250.000 – 350.000
"""

import json
import hashlib
import time
import random
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PRICE_MIN = 250000
PRICE_MAX = 350000
DATA_FILE = Path(__file__).parent.parent / "data" / "properties.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}

def make_id(url): return hashlib.md5(url.encode()).hexdigest()[:12]
def sleep_random(a=2, b=5): time.sleep(random.uniform(a, b))
def now_iso(): return datetime.now(timezone.utc).isoformat()
def parse_surface(text):
    if not text: return None
    m = re.search(r"(\d+)\s*m", text.lower())
    return int(m.group(1)) if m else None

# ── MERCADOLIBRE API ──────────────────────────────────────────────────────────

ML_CATEGORIES = {
    "Casa": "MLA1459", "PH": "MLA1460",
    "Terreno": "MLA1461", "Galpón": "MLA1473", "Depósito": "MLA1472",
}

def scrape_mercadolibre_api():
    results = []
    base_url = "https://api.mercadolibre.com/sites/MLA/search"
    zones_query = ["Vicente Lopez", "San Isidro", "Florida Buenos Aires", "La Lucila"]
    zones_display = ["Vicente López", "San Isidro", "Florida", "La Lucila"]

    for ptype_name, cat_id in ML_CATEGORIES.items():
        for zone_q, zone_name in zip(zones_query, zones_display):
            offset = 0
            page_results = 0
            while True:
                params = {
                    "category": cat_id,
                    "price": f"{PRICE_MIN}-{PRICE_MAX}",
                    "currency_id": "USD",
                    "q": zone_q,
                    "limit": 50,
                    "offset": offset,
                }
                try:
                    r = requests.get(base_url, params=params, timeout=20)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:
                    log.warning(f"[ML API] {ptype_name}/{zone_name} offset {offset}: {e}")
                    break

                items = data.get("results", [])
                if not items:
                    break

                for item in items:
                    try:
                        price = item.get("price")
                        if not price or not (PRICE_MIN <= price <= PRICE_MAX):
                            continue
                        attrs = {a["id"]: a.get("value_name") for a in item.get("attributes", [])}
                        surface_str = attrs.get("TOTAL_AREA") or attrs.get("COVERED_AREA")
                        surface_m2 = parse_surface(surface_str) if surface_str else None
                        rooms = attrs.get("ROOMS")
                        bedrooms = attrs.get("BEDROOMS")
                        rooms_str = f"{rooms} amb." if rooms else (f"{bedrooms} dorm." if bedrooms else None)
                        url = item.get("permalink", "")
                        address = item.get("location", {}).get("address_line") or zone_name
                        results.append({
                            "id": make_id(url),
                            "source": "MercadoLibre",
                            "type": ptype_name,
                            "zone": zone_name,
                            "title": item.get("title", f"{ptype_name} en {zone_name}"),
                            "address": address,
                            "price_usd": int(price),
                            "surface_m2": surface_m2,
                            "rooms": rooms_str,
                            "url": url,
                            "first_seen": now_iso(),
                            "last_seen": now_iso(),
                        })
                        page_results += 1
                    except Exception as e:
                        log.debug(f"Error item ML: {e}")

                total = data.get("paging", {}).get("total", 0)
                offset += 50
                if offset >= min(total, 150):
                    break
                sleep_random(0.5, 1.5)

            log.info(f"[ML API] {ptype_name} en {zone_name}: {page_results} encontradas")
            sleep_random(1, 2)

    log.info(f"[MercadoLibre] {len(results)} propiedades totales")
    return results

# ── ARGENPROP ─────────────────────────────────────────────────────────────────

ARGENPROP_TYPES = {"Casa": "casas", "PH": "ph", "Terreno": "terrenos", "Galpón": "galpones"}
ARGENPROP_ZONES = {
    "Vicente López": ["localidad-vicente-lopez", "partido-vicente-lopez"],
    "San Isidro":    ["localidad-san-isidro", "partido-san-isidro"],
    "Florida":       ["localidad-florida"],
    "La Lucila":     ["localidad-la-lucila"],
}

def scrape_argenprop():
    results = []
    for ptype_name, ptype_slug in ARGENPROP_TYPES.items():
        for zone_name, zone_slugs in ARGENPROP_ZONES.items():
            found = False
            for zone_slug in zone_slugs:
                url = (
                    f"https://www.argenprop.com/{ptype_slug}/venta/{zone_slug}"
                    f"?precio-desde={PRICE_MIN}&precio-hasta={PRICE_MAX}&moneda=dolares"
                )
                log.info(f"[Argenprop] {ptype_name} en {zone_name}")
                try:
                    r = requests.get(url, headers=HEADERS, timeout=20)
                    if r.status_code in (404, 403):
                        continue
                    r.raise_for_status()
                except Exception as e:
                    log.warning(f"[Argenprop] {e}")
                    continue

                soup = BeautifulSoup(r.text, "html.parser")
                cards = soup.select(".card--property") or soup.select(".card") or soup.select("article[class*='card']")

                for card in cards[:30]:
                    try:
                        price_el = card.select_one("[class*='price']")
                        if not price_el: continue
                        price_text = price_el.get_text(strip=True)
                        price_match = re.search(r"(?:USD|U\$S|u\$s)\s*([\d.,]+)", price_text, re.IGNORECASE)
                        if not price_match: continue
                        price = int(re.sub(r"[.,]", "", price_match.group(1)))
                        if price < 1000: price *= 1000
                        if not (PRICE_MIN <= price <= PRICE_MAX): continue

                        link_el = card.select_one("a[href]")
                        href = link_el["href"] if link_el else ""
                        full_url = f"https://www.argenprop.com{href}" if href.startswith("/") else href
                        if not full_url: continue

                        title_el = card.select_one("[class*='title'], h2, h3")
                        addr_el = card.select_one("[class*='address'], [class*='location']")
                        surface_el = card.select_one("[class*='surface'], [class*='area']")

                        results.append({
                            "id": make_id(full_url),
                            "source": "Argenprop",
                            "type": ptype_name,
                            "zone": zone_name,
                            "title": title_el.get_text(strip=True) if title_el else f"{ptype_name} en {zone_name}",
                            "address": addr_el.get_text(strip=True) if addr_el else zone_name,
                            "price_usd": price,
                            "surface_m2": parse_surface(surface_el.get_text()) if surface_el else None,
                            "rooms": None,
                            "url": full_url,
                            "first_seen": now_iso(),
                            "last_seen": now_iso(),
                        })
                        found = True
                    except Exception as e:
                        log.debug(f"Error Argenprop card: {e}")

                if found:
                    break
                sleep_random(2, 4)

            sleep_random(3, 5)

    log.info(f"[Argenprop] {len(results)} propiedades encontradas")
    return results

# ── DEDUP & DIFF ──────────────────────────────────────────────────────────────

def dedup(props):
    seen = {}
    for p in props:
        if p["id"] not in seen:
            seen[p["id"]] = p
    return list(seen.values())

def diff(old_props, new_props):
    old_map = {p["id"]: p for p in old_props}
    new_map = {p["id"]: p for p in new_props}
    new_today     = [p for pid, p in new_map.items() if pid not in old_map]
    removed_today = [p for pid, p in old_map.items() if pid not in new_map]
    price_changes = []
    for pid, new_p in new_map.items():
        if pid in old_map:
            op = old_map[pid].get("price_usd")
            np = new_p.get("price_usd")
            if op and np and op != np:
                price_changes.append({**new_p, "old_price_usd": op,
                    "price_change_pct": round((np - op) / op * 100, 1)})
    return new_today, removed_today, price_changes

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Monitor Inmobiliario GBA Norte ===")

    old_props = []
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE) as f:
                old_data = json.load(f)
                old_props = old_data.get("all_properties", [])
                log.info(f"Cargadas {len(old_props)} propiedades previas")
        except Exception as e:
            log.warning(f"No se pudo cargar data previa: {e}")

    fresh = []
    for name, fn in [("MercadoLibre", scrape_mercadolibre_api), ("Argenprop", scrape_argenprop)]:
        try:
            r = fn()
            fresh.extend(r)
        except Exception as e:
            log.error(f"{name} failed: {e}")

    fresh = dedup(fresh)
    log.info(f"Total dedup: {len(fresh)}")

    old_map = {p["id"]: p for p in old_props}
    for p in fresh:
        if p["id"] in old_map:
            p["first_seen"] = old_map[p["id"]]["first_seen"]

    new_today, removed_today, price_changes = diff(old_props, fresh)
    prices   = [p["price_usd"] for p in fresh if p.get("price_usd")]
    surfaces = [p["surface_m2"] for p in fresh if p.get("surface_m2")]
    ppm2_list = [p["price_usd"]/p["surface_m2"] for p in fresh if p.get("price_usd") and p.get("surface_m2") and p["surface_m2"]>0]

    output = {
        "last_updated": now_iso(),
        "meta": {"zones": ["Vicente López","Florida","La Lucila","San Isidro"],
                 "price_min_usd": PRICE_MIN, "price_max_usd": PRICE_MAX,
                 "types": ["Casa","PH","Terreno","Galpón","Depósito"]},
        "stats": {
            "total": len(fresh), "new_today": len(new_today),
            "removed_today": len(removed_today), "price_changes": len(price_changes),
            "avg_price_usd": int(sum(prices)/len(prices)) if prices else 0,
            "avg_price_per_m2": int(sum(ppm2_list)/len(ppm2_list)) if ppm2_list else 0,
            "avg_surface_m2": int(sum(surfaces)/len(surfaces)) if surfaces else 0,
        },
        "new_today": new_today, "removed_today": removed_today,
        "price_changes": price_changes, "all_properties": fresh,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info(f"✅ Guardado. Total: {len(fresh)} | Nuevas: {len(new_today)} | Bajas: {len(removed_today)} | Cambios: {len(price_changes)}")

if __name__ == "__main__":
    main()
