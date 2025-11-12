"""
Flask app exposing a simple Task API.
- JSON routes with proper status codes and errors
- CORS: only for http://localhost:5500 (local dev)
- DB auto-detection handled in db.py

Serverless on Vercel: export `app` for WSGI.
Local dev: `python api/app.py` or `flask --app api/app.py run`
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Import DB helper functions (backend auto-selected at import)
import db

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['TESTING'] = False

# Enable CORS only for local static server origin
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5500"]}})


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.get("/api/tasks")
def list_tasks():
    tasks = db.get_all_tasks()
    return jsonify(tasks), 200


@app.get("/api/tasks/<int:task_id>")
def get_one(task_id: int):
    task = db.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200


@app.post("/api/tasks")
def create():
    try:
        data = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "'title' is required"}), 400

    task = db.create_task(title)
    return jsonify(task), 201


@app.put("/api/tasks/<int:task_id>")
def update(task_id: int):
    try:
        data = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON body"}), 400

    title = data.get("title")
    done = data.get("done")

    # Only allow bool for done when provided
    if done is not None and not isinstance(done, bool):
        return jsonify({"error": "'done' must be boolean"}), 400

    if title is not None:
        if not isinstance(title, str):
            return jsonify({"error": "'title' must be string"}), 400
        title = title.strip()
        if title == "":
            return jsonify({"error": "'title' cannot be empty"}), 400

    task = db.update_task(task_id, title=title, done=done)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task), 200


@app.delete("/api/tasks/<int:task_id>")
def delete(task_id: int):
    ok = db.delete_task(task_id)
    if not ok:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"status": "deleted"}), 200


if __name__ == "__main__":
    # Dev server for local use
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
