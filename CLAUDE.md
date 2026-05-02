# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Frontend**: HTML, CSS, Vanilla JavaScript (no framework)
- **Backend**: Python + FastAPI
- **Communication**: REST API via `fetch()`

## Commands

### Backend

```bash
# Start dev server (from backend/ directory)
uvicorn main:app --reload

# Run tests
pytest

# Lint and format
ruff check .
ruff format .
```

### Frontend

Static files — open `frontend/index.html` directly in a browser, or serve via FastAPI's `StaticFiles` mount.

## Architecture

```
kyosist/
├── backend/        # FastAPI application
│   ├── main.py     # App entry point, router registration, CORS config
│   └── ...
└── frontend/       # Static HTML/CSS/JS
    ├── index.html
    └── ...
```

- The backend exposes REST endpoints under `/api/`.
- The frontend calls these endpoints using the native `fetch()` API.
- In development, FastAPI runs on `http://localhost:8000`; configure CORS with `CORSMiddleware` to allow requests from the frontend origin.
- In production, FastAPI serves the `frontend/` directory as static files via `StaticFiles`.
