# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Frontend**: HTML, CSS, Vanilla JavaScript (no framework)
- **Backend**: Python + FastAPI
- **Communication**: REST API via `fetch()`

## Commands

### Backend (local dev)

```bash
# Start dev server (from backend/ directory) — also serves public/ as static files
uvicorn main:app --reload

# Or double-click start.bat from the project root
```

### Frontend

Static files live in `public/`. In production they are served by Vercel's CDN automatically.

## Architecture

```
kyosist/
├── api/            # Vercel serverless function
│   └── index.py   # FastAPI app (API routes only)
├── backend/        # Local dev server
│   ├── main.py    # FastAPI app + StaticFiles mount for public/
│   └── requirements.txt
├── public/         # Static HTML/CSS/JS (served by Vercel CDN or local uvicorn)
│   ├── index.html
│   └── main.js
├── requirements.txt  # For Vercel Python runtime
├── vercel.json       # Vercel routing config
└── start.bat         # One-click local launcher (Windows)
```

- REST endpoints are under `/api/`.
- The frontend calls them via relative URL `/api/chat` (works on both localhost and Vercel).
- Local dev: `start.bat` → uvicorn on `http://localhost:8000` (serves `public/` + API).
- Production: Vercel CDN serves `public/`, `api/index.py` handles `/api/*` as serverless function.
