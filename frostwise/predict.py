"""Frostwise core: TabPFN-based frost-date prediction + planting calendar."""
import csv
import datetime
import json
import os
import statistics
import time
import urllib.request

import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DATASET_CSV = os.path.join(DATA_DIR, "frost_dataset.csv")

FEATURES = (
    ["lat", "lon", "elevation"]
    + [f"m{m:02d}" for m in range(1, 13)]
    + ["annual_mean", "coldest_month"]
)

_model_cache = {}


def load_dataset():
    with open(DATASET_CSV, newline="") as f:
        rows = list(csv.DictReader(f))
    X = np.array([[float(r[c]) for c in FEATURES] for r in rows], dtype=np.float64)
    y_frost = np.array([int(r["has_frost"]) for r in rows])
    frost_rows = [r for r in rows if int(r["has_frost"]) == 1]
    Xf = np.array([[float(r[c]) for c in FEATURES] for r in frost_rows], dtype=np.float64)
    y_first = np.array([int(r["first_frost_doy"]) for r in frost_rows])
    y_last = np.array([int(r["last_frost_doy"]) for r in frost_rows])
    return X, y_frost, Xf, y_first, y_last


def get_models():
    """Lazily fit TabPFN models (in-context learning; fit = store context)."""
    if not _model_cache:
        from tabpfn import TabPFNClassifier, TabPFNRegressor

        X, y_frost, Xf, y_first, y_last = load_dataset()
        clf = TabPFNClassifier(device="cpu")
        clf.fit(X, y_frost)
        reg_first = TabPFNRegressor(device="cpu")
        reg_first.fit(Xf, y_first)
        reg_last = TabPFNRegressor(device="cpu")
        reg_last.fit(Xf, y_last)
        _model_cache.update(
            clf=clf, reg_first=reg_first, reg_last=reg_last,
            n_train=len(X), n_frost=len(Xf),
        )
    return _model_cache


def fetch_climate(lat, lon, start="2005-01-01", end="2024-12-31"):
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={lat:.4f}&longitude={lon:.4f}"
        f"&start_date={start}&end_date={end}"
        "&daily=temperature_2m_min&timezone=UTC"
    )
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.load(r)
    elev = data.get("elevation", 0.0) or 0.0
    times, tmins = data["daily"]["time"], data["daily"]["temperature_2m_min"]
    buckets = {m: [] for m in range(1, 13)}
    for t, v in zip(times, tmins):
        if v is not None:
            buckets[int(t[5:7])].append(v)
    mm = [round(statistics.mean(buckets[m]), 2) if buckets[m] else 0.0 for m in range(1, 13)]
    return {
        "lat": lat, "lon": lon, "elevation": round(elev, 1),
        **{f"m{m:02d}": v for m, v in enumerate(mm, 1)},
        "annual_mean": round(statistics.mean(mm), 2),
        "coldest_month": round(min(mm), 2),
    }


def doy_to_date(doy, year=2026):
    base = datetime.date(year, 1, 1)
    return (base + datetime.timedelta(days=int(doy) - 1)).isoformat()


def predict(lat, lon):
    """Return frost prediction + planting calendar for a location."""
    feats = fetch_climate(lat, lon)
    X = np.array([[feats[c] for c in FEATURES]], dtype=np.float64)
    m = get_models()
    has_frost = bool(m["clf"].predict(X)[0])
    proba = m["clf"].predict_proba(X)[0]
    result = {
        "location": {"lat": lat, "lon": lon, "elevation_m": feats["elevation"]},
        "has_frost": has_frost,
        "frost_probability": round(float(max(proba)), 3),
        "model": "TabPFN (open-source tabular foundation model)",
        "training_locations": m["n_train"],
        "data_source": "Open-Meteo archive (ERA5), 2005-2024",
    }
    if has_frost:
        first_doy = int(m["reg_first"].predict(X)[0])
        last_doy = int(m["reg_last"].predict(X)[0])
        # sanity clamp
        first_doy = min(max(first_doy, 240), 365)
        last_doy = min(max(last_doy, 1), 150)
        result["first_frost"] = {"doy": first_doy, "date": doy_to_date(first_doy)}
        result["last_frost"] = {"doy": last_doy, "date": doy_to_date(last_doy)}
        result["planting_calendar"] = planting_calendar(last_doy, first_doy)
    else:
        result["planting_calendar"] = planting_calendar(None, None)
    return result


CROPS = [
    # name, hardiness, sow offset vs last frost (weeks; negative = before), notes
    ("Tomato", "tender", 2, "Transplant after last frost; needs warm soil."),
    ("Pepper", "tender", 3, "Needs the warmest spot; transplant late."),
    ("Basil", "tender", 2, "Hates cold; sow after nights stay warm."),
    ("Cucumber", "tender", 1, "Direct sow after last frost."),
    ("Beans", "tender", 1, "Direct sow in warm soil."),
    ("Carrot", "hardy", -3, "Sow 3 weeks before last frost."),
    ("Spinach", "hardy", -4, "Cold-loving; sow 4 weeks before last frost."),
    ("Kale", "hardy", -3, "Improves after light frost."),
    ("Garlic", "hardy", None, "Plant 4-6 weeks before first autumn frost."),
    ("Lettuce", "half-hardy", -2, "Sow 2 weeks before last frost."),
    ("Onion sets", "hardy", -4, "Plant as soon as soil is workable."),
    ("Zucchini", "tender", 1, "Direct sow after last frost."),
]


def planting_calendar(last_doy, first_doy):
    """Rule-based sowing windows anchored on predicted frost dates."""
    cal = []
    base_year = 2026
    for name, hardiness, offset_wks, notes in CROPS:
        if last_doy is None:
            window = "Year-round (no frost at this location)"
        elif name == "Garlic":
            d = datetime.date(base_year, 1, 1) + datetime.timedelta(days=first_doy - 1 - 35)
            window = f"Around {d.isoformat()} (5 weeks before first frost)"
        else:
            d = datetime.date(base_year, 1, 1) + datetime.timedelta(days=last_doy - 1 + offset_wks * 7)
            rel = "after last frost" if offset_wks >= 0 else "before last frost"
            window = f"Around {d.isoformat()} ({abs(offset_wks)} wk {rel})"
        cal.append({"crop": name, "hardiness": hardiness, "sow_window": window, "notes": notes})
    return cal
