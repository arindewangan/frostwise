# Frostwise — DEV Submission Copy
Event: DEV Hacktoberfest AI Challenge — Week 1: Touch Grass

## Title
Frostwise — know your frost dates, plant with confidence

## Tagline
A hyperlocal garden planner that predicts your first and last frost with TabPFN, the open-source tabular foundation model — then tells you exactly when to sow.

## Inspiration
Every gardener knows the heartbreak: a surprise late frost wipes out weeks of seedlings overnight. Frost dates are the single most important number in gardening, yet most people guess them from a vague zone map or a neighbor's memory. I wanted a tool that computes *your* frost dates from real climate history — and turns them into a planting plan you can actually follow.

## What it does
Type any city (or tap a sample like Chicago, Berlin, Bengaluru, Sydney, Tokyo) and Frostwise:
- pulls 20 years of daily minimum temperatures for your location from the Open-Meteo archive (ERA5 reanalysis),
- runs **TabPFN** — the open-source tabular foundation model — to predict whether your location gets frost at all, and if so, your **last spring frost** and **first autumn frost** dates,
- generates a **planting calendar for 12 common crops** (tomatoes, peppers, kale, garlic, spinach…), with sow windows anchored to your predicted frost dates and honest notes per crop.

No frost where you live? It tells you that too — the model learned it from the data, and you get a year-round growing calendar instead.

## How we built it
A Python/Flask backend with a clean single-page frontend. The pipeline: `data/build_dataset.py` fetches 2005–2024 daily minimums for 80 stratified global locations and derives per-location labels (median first/last frost day-of-year, frost = daily min ≤ 0°C) plus 17 climate features. At request time, TabPFN performs the whole prediction **in-context** — a classifier for frost/no-frost, two regressors for the dates — in a single forward pass per model, no gradient training. The frontend is vanilla HTML/CSS/JS; the GitHub Pages demo bakes real precomputed TabPFN predictions (labeled with the build date) so it works without a backend.

## Challenges we ran into
The honest hard part was making the AI *real* instead of decorative. A frost date isn't in any API — it has to be derived, so I built the entire label pipeline from raw reanalysis data and had to get the day-of-year statistics right across hemispheres (autumn frost in Sydney falls in a different part of the year than in Berlin). Tropical locations needed genuine "no frost" handling rather than a hardcoded hack — hence the two-stage classifier + regressor design. The other fight was practical: PyTorch's download servers kept timing out, so the environment setup needed patient retries and mirror fallbacks.

## Accomplishments that we're proud of
- A **real** open-source-AI core: TabPFN inference on real ERA5 data, reproducible end-to-end from this repo — no API keys, no proprietary models, no fake "AI" labels.
- The two-stage design (frost/no-frost classifier → date regressors) that handles everything from Chicago winters to Bengaluru's frost-free climate without special cases.
- A static demo that stays honest: every number is a genuine precomputed inference, clearly labeled as such.
- Clean, readable UI that a non-technical gardener can actually use.

## What we learned
TabPFN's in-context learning is remarkably well suited to small, high-signal tabular problems — 80 locations were enough to learn a physically sensible climate→frost mapping. I also learned that the unglamorous half of "AI projects" is data plumbing: deriving trustworthy labels from raw observations mattered more than any model choice. And that honesty in demos (labeling precomputed vs live) costs nothing and buys trust.

## What's next for Frostwise
Per-crop frost-*damage* risk (not just dates), user-saved locations with frost alerts, Southern-Hemisphere season handling in the calendar copy, and a TabPFN uncertainty readout (prediction intervals) so gardeners see the confidence behind each date.

## Built with
Python, Flask, TabPFN (open-source), Open-Meteo / ERA5, JavaScript

## Links
- GitHub: https://github.com/arindewangan/frostwise
- Live demo: https://arindewangan.github.io/frostwise/demo/
- Video: (YouTube unlisted — link to be added)

## How it uses open-source AI (1 paragraph for the form)
Frostwise's prediction engine is TabPFN (Apache-2.0, PriorLabs) — an open-source tabular foundation model that performs supervised learning in a single forward pass. We derive frost-date labels from 20 years of open ERA5 reanalysis data (via Open-Meteo's free archive), and TabPFN learns the climate→frost-date mapping in-context at inference time: a classifier predicts frost occurrence and two regressors predict first/last frost day-of-year. No proprietary models or API keys are involved anywhere in the pipeline.
