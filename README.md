# Frostwise

**Know your frost dates. Plant with confidence.**

Frostwise is a hyperlocal garden planner that predicts your **first and last frost dates** using [TabPFN](https://github.com/PriorLabs/TabPFN) — the open-source tabular foundation model — trained in-context on 20 years of real ERA5 climate history, then generates a **planting calendar** for 12 common crops anchored to those dates.

Built for [DEV's Hacktoberfest AI Challenge — Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05).

## How it works

1. **Data** — Daily minimum temperatures (2005–2024) for 80 stratified global locations from the Open-Meteo archive API (ERA5 reanalysis; free, no key). See `data/build_dataset.py`.
2. **Labels** — Per location, the median first-autumn-frost and last-spring-frost day-of-year (frost = daily min ≤ 0°C), plus monthly climate features.
3. **Model** — TabPFN (open-source, PriorLabs) learns the climate → frost-date mapping **in-context**: a classifier predicts *whether* a location gets frost; two regressors predict *when*. Real inference runs at request time — no gradient training, no black box.
4. **Calendar** — Predicted frost dates anchor a rule-based sowing calendar (12 crops, frost-tender vs hardy).

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cpu/
pip install tabpfn flask requests numpy pandas
python app.py   # → http://127.0.0.1:5050
```

The dataset (`data/frost_dataset.csv`) is bundled; TabPFN downloads its open weights on first run.

## Project layout

```
app.py                  # Flask app (geocode + predict API)
frostwise/
  predict.py            # TabPFN inference + planting calendar
  static/index.html     # web UI
data/
  build_dataset.py      # dataset builder (Open-Meteo → frost_dataset.csv)
  frost_dataset.csv     # 80 locations, 2005–2024 (generated)
demo/
  build_demo.py         # bakes real TabPFN predictions into demo/index.html
  index.html            # static demo for GitHub Pages (precomputed, labeled)
```

## Honesty notes

- Predictions are **statistical estimates from historical climate**, not weather forecasts. Microclimates (urban heat islands, valleys, elevation pockets) can shift real frost by days.
- The static demo page uses **precomputed** TabPFN predictions (labeled with the build date); the Flask app runs **live inference** per request.
- Tropical locations genuinely get "no frost expected" — the classifier learned that, we didn't hardcode it.

## Open-source AI at its core

Frostwise's entire prediction engine is [TabPFN](https://github.com/PriorLabs/TabPFN) (Apache-2.0, PriorLabs) — a tabular foundation model that performs supervised learning in a single forward pass. Climate data comes from Open-Meteo's free archive (ERA5). No proprietary models, no API keys, no black boxes: the full pipeline from raw reanalysis data to frost date is reproducible from this repo.

## License

MIT
