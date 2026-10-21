"""PART 2: the API. Run: python app.py  (after seed_db.py)"""
import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

DB = Path(__file__).resolve().parent / "restaurants.db"
app = Flask(__name__)
CORS(app)

# Edit these price ranges to suit your Swiggy data
BUDGETS = {"low": (0, 300), "medium": (301, 700), "high": (701, 1000000)}
CATEGORY_COLUMN = {"comfort food": "is_comfort", "protein bowl": "is_protein"}

def query(sql, args=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()

@app.get("/api/health")
def health():
    return jsonify(ok=True)

@app.post("/api/recommend")
def recommend():
    p = request.get_json(silent=True) or {}
    cuisine = str(p.get("cuisine", "")).strip()
    category = p.get("category")
    budget = p.get("budget")
    area = str(p.get("area", "")).strip()
    allergies = {str(a).lower() for a in p.get("allergies", [])}

    if not cuisine or category not in CATEGORY_COLUMN or budget not in BUDGETS:
        return jsonify(error="Please choose a cuisine, a food type and a budget."), 400

    low, high = BUDGETS[budget]
    restaurants = query(
        """SELECT * FROM restaurants
           WHERE cuisine LIKE ? AND (area LIKE ? OR location LIKE ?) AND price BETWEEN ? AND ?
           ORDER BY rating DESC, number_of_ratings DESC LIMIT 6""",
        (f"%{cuisine}%", f"%{area}%", f"%{area}%", low, high))

    col = CATEGORY_COLUMN[category]   # safe: comes from the fixed whitelist above
    candidates = query(
        f"SELECT * FROM dishes WHERE cuisine = ? COLLATE NOCASE AND {col} = 1 ORDER BY RANDOM() LIMIT 100",
        (cuisine,))
    safe = [d for d in candidates if not allergies & set(filter(None, d["allergens"].split(";")))]

    return jsonify(restaurants=restaurants, dishes=safe[:3], searched_dishes=len(candidates))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
