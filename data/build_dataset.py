#!/usr/bin/env python3
"""Build the frost-date training dataset v2 — curated cities, not ocean points.

For a curated list of global cities across climate zones, fetches 2005-2024
daily minimum temperatures from the Open-Meteo archive API (free, no key),
then computes per-city climate features and median first/last frost day-of-year.

Output: data/frost_dataset.csv
"""
import csv
import json
import statistics
import sys
import time
import urllib.request

START_YEAR = 2005
END_YEAR = 2024
OUT_CSV = "data/frost_dataset.csv"
OUT_META = "data/dataset_meta.json"

# (name, lat, lon) — curated for climate diversity, all land
CITIES = [
    # Temperate — definite frost
    ("Chicago", 41.8781, -87.6298), ("Berlin", 52.52, 13.405),
    ("Toronto", 43.6532, -79.3832), ("Moscow", 55.7558, 37.6173),
    ("Beijing", 39.9042, 116.4074), ("London", 51.5074, -0.1278),
    ("Paris", 48.8566, 2.3522), ("New York", 40.7128, -74.0060),
    ("Seoul", 37.5665, 126.9780), ("Tokyo", 35.6762, 139.6503),
    ("Madrid", 40.4168, -3.7038), ("Warsaw", 52.2297, 21.0122),
    ("Stockholm", 59.3293, 18.0686), ("Minneapolis", 44.9778, -93.2650),
    ("Denver", 39.7392, -104.9903), ("Zurich", 47.3769, 8.5417),
    ("Vienna", 48.2082, 16.3738), ("Prague", 50.0755, 14.4378),
    ("Amsterdam", 52.3676, 4.9041), ("Dublin", 53.3498, -6.2603),
    ("Boston", 42.3601, -71.0589), ("Montreal", 45.5017, -73.5673),
    ("Oslo", 59.9139, 10.7522), ("Helsinki", 60.1699, 24.9384),
    ("Edmonton", 53.5461, -113.4938), ("Ulaanbaatar", 47.8864, 106.9057),
    ("Harbin", 45.8038, 126.5350), ("Sapporo", 43.0618, 141.3545),
    # Mild temperate — marginal frost
    ("Sydney", -33.8688, 151.2093), ("Melbourne", -37.8136, 144.9631),
    ("Auckland", -36.8485, 174.7633), ("Cape Town", -33.9249, 18.4241),
    ("Buenos Aires", -34.6037, -58.3816), ("Santiago", -33.4489, -70.6693),
    ("Rome", 41.9028, 12.4964), ("Athens", 37.9838, 23.7275),
    ("Lisbon", 38.7223, -9.1393), ("Los Angeles", 34.0522, -118.2437),
    ("San Francisco", 37.7749, -122.4194), ("Perth", -31.9505, 115.8605),
    ("Adelaide", -34.9285, 138.6007), ("Portland", 45.5152, -122.6784),
    ("Vancouver", 49.2827, -123.1207), ("Seattle", 47.6062, -122.3321),
    # Subtropical — light/rare frost
    ("Delhi", 28.6139, 77.2090), ("Cairo", 30.0444, 31.2357),
    ("Phoenix", 33.4484, -112.0740), ("Houston", 29.7604, -95.3698),
    ("New Orleans", 29.9511, -90.0715), ("Shanghai", 31.2304, 121.4737),
    ("Johannesburg", -26.2041, 28.0473), ("Mexico City", 19.4326, -99.1332),
    ("Sao Paulo", -23.5558, -46.6396), ("Brisbane", -27.4698, 153.0251),
    # Tropical — no frost
    ("Bengaluru", 12.9719, 77.5937), ("Singapore", 1.3521, 103.8198),
    ("Lagos", 6.5244, 3.3792), ("Jakarta", -6.2088, 106.8456),
    ("Mumbai", 19.0760, 72.8777), ("Bangkok", 13.7563, 100.5018),
    ("Nairobi", -1.2921, 36.8219), ("Lima", -12.0464, -77.0428),
    ("Rio de Janeiro", -22.9068, -43.1729), ("Manila", 14.5995, 120.9842),
    ("Kuala Lumpur", 3.1390, 101.6869), ("Darwin", -12.4634, 130.8456),
    ("Honolulu", 21.3099, -157.8581), ("Quito", -0.1807, -78.4678),
    ("Bogota", 4.7110, -74.0721),
]


def fetch_archive(lat, lon, retries=3):
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat:.4f}&longitude={lon:.4f}"
        f"&start_date={START_YEAR}-01-01&end_date={END_YEAR}-12-31"
        "&daily=temperature_2m_min&timezone=UTC"
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 * (attempt + 1))


def frost_stats(daily):
    times, tmins = daily["time"], daily["temperature_2m_min"]
    by_year = {}
    for t, v in zip(times, tmins):
        if v is None:
            continue
        doy = time.strptime(t, "%Y-%m-%d").tm_yday
        by_year.setdefault(t[:4], []).append((doy, v))
    firsts, lasts, frost_years = [], [], 0
    for rows in by_year.values():
        frost_days = [doy for doy, v in rows if v <= 0.0]
        if not frost_days:
            continue
        frost_years += 1
        autumn = [d for d in frost_days if d >= 240]
        spring = [d for d in frost_days if d <= 150]
        if autumn:
            firsts.append(min(autumn))
        if spring:
            lasts.append(max(spring))
    n_years = len(by_year)
    has_frost = frost_years >= max(1, n_years // 2)
    return (
        has_frost,
        int(statistics.median(firsts)) if firsts else -1,
        int(statistics.median(lasts)) if lasts else -1,
    )


def main():
    rows = []
    for i, (name, lat, lon) in enumerate(CITIES, 1):
        print(f"[{i}/{len(CITIES)}] {name} ...", flush=True)
        try:
            data = fetch_archive(lat, lon)
        except Exception as e:
            print(f"  SKIP ({e})")
            continue
        daily = data.get("daily")
        if not daily or not daily.get("time"):
            print("  SKIP (no data)")
            continue
        elev = data.get("elevation", 0.0) or 0.0
        buckets = {m: [] for m in range(1, 13)}
        for t, v in zip(daily["time"], daily["temperature_2m_min"]):
            if v is not None:
                buckets[int(t[5:7])].append(v)
        mm = [round(statistics.mean(buckets[m]), 2) if buckets[m] else 0.0 for m in range(1, 13)]
        has_frost, first_doy, last_doy = frost_stats(daily)
        rows.append({
            "city": name, "lat": lat, "lon": lon, "elevation": round(elev, 1),
            **{f"m{m:02d}": v for m, v in enumerate(mm, 1)},
            "annual_mean": round(statistics.mean(mm), 2),
            "coldest_month": round(min(mm), 2),
            "has_frost": int(has_frost),
            "first_frost_doy": first_doy,
            "last_frost_doy": last_doy,
        })
        time.sleep(0.3)
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    frost_n = sum(r["has_frost"] for r in rows)
    with open(OUT_META, "w") as f:
        json.dump({
            "n_locations": len(rows),
            "n_frost": frost_n,
            "n_no_frost": len(rows) - frost_n,
            "years": f"{START_YEAR}-{END_YEAR}",
            "source": "Open-Meteo archive API (ERA5)",
        }, f, indent=2)
    print(f"Wrote {OUT_CSV}: {len(rows)} rows ({frost_n} frost)")


if __name__ == "__main__":
    sys.exit(main())
