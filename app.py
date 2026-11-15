import csv, io, os, sqlite3
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(APP_DIR, "data", "deals.db"))
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "5"))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-public-deployment")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

def db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                original_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                product_url TEXT DEFAULT '',
                image_url TEXT DEFAULT '',
                retailer TEXT DEFAULT 'Amazon',
                category TEXT DEFAULT '',
                source TEXT DEFAULT 'CSV import',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

def clean_price(value):
    if value is None: raise ValueError("Missing price")
    cleaned = str(value).strip().replace("$", "").replace(",", "")
    price = float(cleaned)
    if price < 0 or price > 100000000: raise ValueError("Invalid price")
    return round(price, 2)

def add_deal(row, source="CSV import"):
    title = str(row.get("title", row.get("name", ""))).strip()
    if not title: raise ValueError("Product title is required")
    original = clean_price(row.get("original_price", row.get("list_price")))
    sale = clean_price(row.get("sale_price", row.get("deal_price")))
    if original <= 0: raise ValueError("Original price must be greater than zero")
    if sale > original: raise ValueError("Sale price cannot exceed original price")
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute("""
            INSERT INTO deals(title, original_price, sale_price, product_url, image_url,
                              retailer, category, source, created_at, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (title, original, sale, str(row.get("product_url", row.get("url", ""))).strip(),
              str(row.get("image_url", "")).strip(),
              str(row.get("retailer", "Amazon")).strip() or "Amazon",
              str(row.get("category", "")).strip(), source, now, now))

@app.route("/")
def index():
    with db() as conn:
        rows = conn.execute("SELECT * FROM deals").fetchall()
    deals = []
    for r in rows:
        d = dict(r)
        d["discount_pct"] = round((d["original_price"] - d["sale_price"]) / d["original_price"] * 100, 1)
        d["savings"] = round(d["original_price"] - d["sale_price"], 2)
        deals.append(d)
    deals.sort(key=lambda x: (-x["discount_pct"], x["sale_price"], x["title"].lower()))
    return render_template("index.html", deals=deals, count=len(deals),
                           avg=round(sum(x["discount_pct"] for x in deals)/len(deals),1) if deals else 0)

@app.post("/import")
def import_csv():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a CSV file first.", "error"); return redirect(url_for("index"))
    if not file.filename.lower().endswith(".csv"):
        flash("Only CSV files are supported.", "error"); return redirect(url_for("index"))
    try:
        text = file.stream.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required = {"title", "original_price", "sale_price"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV needs these columns: title, original_price, sale_price. Optional: product_url, image_url, retailer, category.")
        added, errors = 0, []
        for line, row in enumerate(reader, start=2):
            try:
                add_deal(row)
                added += 1
            except Exception as e:
                errors.append(f"Line {line}: {e}")
        message = f"Imported {added} deal(s)."
        if errors: message += " " + " | ".join(errors[:5])
        flash(message, "success" if added else "error")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("index"))

@app.post("/add")
def add_manual():
    try:
        add_deal(request.form, source="Manual")
        flash("Deal added.", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect(url_for("index"))

@app.post("/delete/<int:deal_id>")
def delete(deal_id):
    with db() as conn: conn.execute("DELETE FROM deals WHERE id=?", (deal_id,))
    return redirect(url_for("index"))

@app.post("/clear")
def clear():
    with db() as conn: conn.execute("DELETE FROM deals")
    flash("All listings removed.", "success")
    return redirect(url_for("index"))

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.errorhandler(413)
def too_large(_):
    flash(f"Upload exceeds {MAX_UPLOAD_MB} MB.", "error")
    return redirect(url_for("index"))

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
