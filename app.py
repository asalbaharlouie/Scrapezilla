import time
import threading

from digiscraper import scrape_products
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

job_lock = threading.Lock()

job = {
    "running": False,
    "method": None,
    "category": None,
    "brand": None,
    "status": "Ready to start",
    "progress": 0,
    "total_pages": 0,
    "products_count": 0,
    "elapsed": None,
    "error": None,
    "results": [],
}


@app.get("/")
def index():
    return render_template("index.html")


def run_scraping(method, category, brand, pages):
    start_time = time.time()

    try:
        def update_progress(done, total, count, status_message):
            with job_lock:
                job["progress"] = done
                job["total_pages"] = total
                job["products_count"] = count
                job["status"] = status_message

        collected_products = scrape_products(
            category=category,
            brand=brand,
            max_pages=pages,
            progress_callback=update_progress,
        )

        products = list(collected_products.values())
        elapsed = round(time.time() - start_time, 2)

        with job_lock:
            job["results"] = products[:10]
            job["products_count"] = len(products)
            job["elapsed"] = elapsed
            job["progress"] = job["total_pages"]
            job["status"] = "Completed successfully"
            job["error"] = None

    except Exception as error:
        with job_lock:
            job["status"] = "Scraping failed"
            job["error"] = str(error)

    finally:
        with job_lock:
            job["running"] = False


@app.post("/api/start")
def start_scraping():
    data = request.get_json(silent=True) or {}

    method = data.get("method", "threading")
    category = data.get("category", "mobile-phone")
    brand = data.get("brand", "samsung")

    if not isinstance(category, str) or not category.strip():
        return jsonify({"error": "Please select a category."}), 400

    if not isinstance(brand, str) or not brand.strip():
        return jsonify({"error": "Please select a brand."}), 400

    category = category.strip()
    brand = brand.strip()

    # Validate pages before converting the value to an integer.
    raw_pages = data.get("pages", 3)

    if isinstance(raw_pages, bool) or isinstance(raw_pages, float):
        return jsonify({"error": "Pages must be an integer."}), 400

    try:
        pages = int(raw_pages)
    except (TypeError, ValueError):
        return jsonify({"error": "Pages must be an integer."}), 400

    # Reject decimal strings such as "1.5" and "3.0".
    if isinstance(raw_pages, str) and str(pages) != raw_pages.strip():
        return jsonify({"error": "Pages must be an integer."}), 400

    if method not in ("threading", "async"):
        return jsonify({"error": "Invalid scraping method."}), 400

    if not 1 <= pages <= 10:
        return jsonify({"error": "Choose between 1 and 10 pages."}), 400

    with job_lock:
        if job["running"]:
            return jsonify({
                "error": "A scraping job is already running."
            }), 409

        job.update({
            "running": True,
            "method": method,
            "category": category,
            "brand": brand,
            "status": "Starting...",
            "progress": 0,
            "total_pages": pages,
            "products_count": 0,
            "elapsed": None,
            "error": None,
            "results": [],
        })

    worker = threading.Thread(
        target=run_scraping,
        args=(method, category, brand, pages),
        daemon=True,
    )
    worker.start()

    return jsonify({"message": "Scraping started."})


@app.get("/api/status")
def scraping_status():
    with job_lock:
        return jsonify(dict(job))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
