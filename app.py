"""Frostwise web app: TabPFN frost-date predictions + planting calendar."""
import json
import os
import urllib.parse
import urllib.request

from flask import Flask, jsonify, request, send_from_directory

from frostwise.predict import predict

app = Flask(__name__, static_folder="static", static_url_path="/static")
ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return send_from_directory(os.path.join(ROOT, "static"), "index.html")


@app.route("/api/geocode")
def geocode():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "missing q"}), 400
    url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        + urllib.parse.urlencode({"name": q, "count": 6, "language": "en", "format": "json"})
    )
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    out = [
        {
            "name": x.get("name"),
            "country": x.get("country"),
            "admin1": x.get("admin1"),
            "lat": x.get("latitude"),
            "lon": x.get("longitude"),
        }
        for x in data.get("results", [])
    ]
    return jsonify(out)


@app.route("/api/predict")
def api_predict():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat/lon required"}), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "lat/lon out of range"}), 400
    try:
        return jsonify(predict(lat, lon))
    except Exception as e:  # noqa: BLE001 - surface as JSON for the UI
        return jsonify({"error": f"prediction failed: {e}"}), 502


@app.route("/api/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
