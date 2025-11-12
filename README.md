# Mini Project: Task Manager (Flask + Vanilla JS) 

A beginner-friendly Task Manager with a Flask backend and a vanilla HTML/CSS/JS frontend. Runs locally and deploys to Vercel using Python Serverless Functions.

## Features
- Flask API with JSON routes (GET/POST/PUT/DELETE)
- Tiny DB layer that auto-detects Postgres → SQLite → in-memory
- Vanilla frontend with fetch, form to add tasks, and actions: Toggle / Edit / Delete
- pytest tests with Flask test client
- Vercel serverless deployment (api/app.py)

## Project Structure
```
mini-project/
  vercel.json
  requirements.txt
  README.md
  tests/
    test_api.py
  backend/
    db_init.py
  api/
    app.py
    db.py
  frontend/
    index.html
    styles.css
    app.js
```

## Local Development

### 1) Python env and dependencies
- Create and activate a virtualenv (Windows PowerShell):
  - `python -m venv .venv`
  - `.venv\\Scripts\\Activate.ps1`
- Install deps:
  - `pip install -r requirements.txt`

### 2) Initialize local SQLite with seed data (optional, for persistence locally)
- `python backend/db_init.py`
- This creates `backend/tasks.db` and seeds 3 tasks.

### 3) Run the Flask API
- Option A (Flask CLI): `flask --app api/app.py run`
- Option B (Python): `python api/app.py`

The API will run on `http://127.0.0.1:5000`.

### 4) Run the frontend (static server)
- From the `frontend/` folder: `python -m http.server 5500`
- Open `http://localhost:5500` in your browser.

### CORS note
- CORS is enabled for `http://localhost:5500` only (development).
- On Vercel, the frontend and API share the same domain, so no special CORS is required.
- In `frontend/app.js`, `API_BASE` is set to empty string so calls go to `/api/...` in production. For local dev, see the comment to point to `http://127.0.0.1:5000` if you directly call the backend.

### Running tests
- `pytest -q`
- Tests use the in-memory backend by setting an env var just for the test run.

## Deploy to Vercel
1. `vercel login`
2. From the project root: `vercel` (first-time link) then `vercel --prod` for production.
3. If you want persistence on Vercel, set environment variable `DATABASE_URL` (e.g., Vercel Postgres URL).
   - Without `DATABASE_URL`, the API falls back to an in-memory store (ephemeral; resets every cold start).

### vercel.json
Routes `/api/*` to the Flask serverless function, and everything else to the static frontend index.html.
```json
{
  "routes": [
    { "src": "^/api/.*", "dest": "api/app.py" },
    { "src": "^/$", "dest": "frontend/index.html" },
    { "src": "^(?!/api/).*$", "dest": "frontend/index.html" }
  ]
}
```

## Storage on Vercel (Important)
- Vercel serverless functions have ephemeral filesystem. Do not rely on local files there.
- For persistence, use a remote DB like Vercel Postgres.
- This project auto-detects DB in this order:
  - Postgres via `DATABASE_URL` (psycopg2)
  - Local SQLite file `backend/tasks.db` (for development)
  - In-memory dict fallback (stateless on Vercel without `DATABASE_URL`)

## Improvements to try next
- Add pagination and search
- Add due dates and priorities
- Add authentication
- Add better error boundaries and retries in the frontend
