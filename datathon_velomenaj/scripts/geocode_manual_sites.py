import time
import sys
from datetime import datetime

import folium
import os 

import pandas as pd
import requests

MANUAL_COUNTS_CSV = "data/bronze/comptage_manuel/comptage_manuel_clean.csv"
OUT_CSV = "data/bronze/comptage_manuel/manual_sites_geo.csv"

# ----------------------------
# Helpers (logs)
# ----------------------------
def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

# ----------------------------
# Hardcoded fallbacks + coords
# ----------------------------

# 1) fallback "address_query" (quand le nom court ne marche pas)
FALLBACK_ADDRESS = {
    "Bas Montée Bonnafous": "Place Louis Chazette / Montée Bonnafous, 69004 Lyon, France",
    "Bas Montée St Sébastien": "Montée Saint-Sébastien, 69001 Lyon, France",
    "Bvd des Canuts": "Boulevard des Canuts, 69004 Lyon, France",
    "Carrefour St Clair": "2 Montée des Soldats, 69300 Caluire-et-Cuire, France",
    "Croisement Bonnafous/Herbouville": "Place Louis Chazette, 69004 Lyon, France",
    "Margnolles / Oratoire": "6 Rue de l'Oratoire, 69300 Caluire-et-Cuire, France",
    "Pont Fontaines RG": "Pont de Fontaines-sur-Saône, 69270 Fontaines-sur-Saône, France",
    "Quai Clémenceau/Castellane": "Montée Castellane, 69300 Caluire-et-Cuire, France",
}

# 2) coordonnées hardcodées si Nominatim ne trouve toujours pas
# Bas Montée Bonnafous / Croisement Bonnafous-Herbouville : Place Louis Chazette (coordonnées Wikipedia photo) :contentReference[oaicite:0]{index=0}
# Carrefour St Clair : géoloc trouvée pour "2 Montée des Soldats" :contentReference[oaicite:1]{index=1}
# Margnolles/Oratoire : coordonnées sur "4 Rue de Margnolles" (BRGM fiche risques) :contentReference[oaicite:2]{index=2}
# Quai Clémenceau/Castellane : Montée Castellane (coords) :contentReference[oaicite:3]{index=3}
HARDCODED_COORDS = {
    "Bas Montée Bonnafous": (45.7737583, 4.8382250),
    "Croisement Bonnafous/Herbouville": (45.7737583, 4.8382250),
    "Carrefour St Clair": (45.79862735, 4.85747306503),
    "Margnolles / Oratoire": (45.79092055, 4.8465445733814),
    "Quai Clémenceau/Castellane": (45.799144, 4.846415),
}

# ----------------------------
# Nominatim (avec retry)
# ----------------------------
URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "lyon-cycling-project/1.0 (contact: younessetahiri01@gmail.com)"}

def nominatim_search(session: requests.Session, q: str, limit: int = 3, timeout: int = 20, retries: int = 2):
    params = {"q": q, "format": "json", "limit": limit}
    last_err = None
    for attempt in range(retries + 1):
        try:
            r = session.get(URL, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json(), None
        except Exception as e:
            last_err = e
            # backoff simple
            sleep_s = 2 * (attempt + 1)
            log(f"   ↳ WARN attempt {attempt+1}/{retries+1} failed: {e} (sleep {sleep_s}s)")
            time.sleep(sleep_s)
    return None, last_err

# ----------------------------
# Main
# ----------------------------
def main():
    log("Starting manual sites geocoding")
    log("Reading manual counts CSV")

    df = pd.read_csv(MANUAL_COUNTS_CSV)
    sites = sorted(df["Point comptage"].dropna().astype(str).str.strip().unique())

    log(f"Found {len(sites)} unique manual sites")

    session = requests.Session()
    session.headers.update(HEADERS)

    results = []
    ok = nf = err = fb_used = hc_used = 0

    for i, name in enumerate(sites, start=1):
        name = str(name).strip()
        log(f"[{i}/{len(sites)}] Geocoding: '{name}'")

        # 1) normal query
        q_normal = f"{name}, Lyon, France"
        data, e = nominatim_search(session, q_normal)

        if data and len(data) > 0:
            best = data[0]
            lat = float(best["lat"])
            lon = float(best["lon"])
            results.append({
                "manual_site_name": name,
                "address_query": q_normal,
                "lat": lat,
                "lon": lon,
                "display_name": best.get("display_name", ""),
                "status": "ok",
                "n_candidates": len(data),
                "mode": "normal",
            })
            ok += 1
            log(f"   ↳ OK [normal] ({lat:.7f}, {lon:.7f})")
            time.sleep(1.0)
            continue

        # 2) fallback address (si défini)
        fb = FALLBACK_ADDRESS.get(name)
        if fb:
            log(f"   ↳ NOT FOUND → fallback: '{fb}'")
            data2, e2 = nominatim_search(session, fb)

            if data2 and len(data2) > 0:
                best = data2[0]
                lat = float(best["lat"])
                lon = float(best["lon"])
                results.append({
                    "manual_site_name": name,
                    "address_query": fb,
                    "lat": lat,
                    "lon": lon,
                    "display_name": best.get("display_name", ""),
                    "status": "ok_fallback",
                    "n_candidates": len(data2),
                    "mode": "fallback",
                })
                ok += 1
                fb_used += 1
                log(f"   ↳ OK [fallback] ({lat:.7f}, {lon:.7f})")
                time.sleep(1.0)
                continue
            else:
                log("   ↳ NOT FOUND (even after fallback)")

        # 3) hardcoded coords (dernier recours)
        if name in HARDCODED_COORDS:
            lat, lon = HARDCODED_COORDS[name]
            results.append({
                "manual_site_name": name,
                "address_query": fb if fb else q_normal,
                "lat": float(lat),
                "lon": float(lon),
                "display_name": "",
                "status": "hardcoded",
                "n_candidates": 0,
                "mode": "hardcoded",
            })
            hc_used += 1
            log(f"   ↳ HARDCODED ({lat:.7f}, {lon:.7f})")
            time.sleep(0.2)
            continue

        # 4) error vs not_found
        if e is not None:
            results.append({
                "manual_site_name": name,
                "address_query": q_normal,
                "status": "error",
                "error": str(e),
            })
            err += 1
            log(f"   ↳ ERROR: {e}")
        else:
            results.append({
                "manual_site_name": name,
                "address_query": q_normal,
                "status": "not_found",
            })
            nf += 1
            log("   ↳ NOT FOUND")

        time.sleep(1.0)

    out = pd.DataFrame(results)
    out.to_csv(OUT_CSV, index=False)

    log("Geocoding finished")
    log(f"Results: OK={ok}, NOT_FOUND={nf}, ERROR={err}, FALLBACK_USED={fb_used}, HARDCODED_USED={hc_used}")
    log(f"Output written to: {OUT_CSV}")
    log("Status counts:\n" + str(out["status"].value_counts()))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Interrupted by user (Ctrl+C)")
        sys.exit(1)

MAP_OUT = "exports/leaflet/manual_sites_preview.html"
os.makedirs(os.path.dirname(MAP_OUT), exist_ok=True)

geo = pd.read_csv("data/bronze/comptage_manuel/manual_sites_geo.csv")

m = folium.Map(location=[45.77, 4.83], zoom_start=12)

for _, r in geo.iterrows():
    if r.get("status") in ("ok", "ok_fallback", "hardcoded"):
        folium.Marker(
            location=[r["lat"], r["lon"]],
            popup=f"""
            <b>{r['manual_site_name']}</b><br>
            status: {r['status']}<br>
            {r.get('display_name','')}
            """
        ).add_to(m)

m.save(MAP_OUT)
print(f"✅ map saved: {MAP_OUT}")