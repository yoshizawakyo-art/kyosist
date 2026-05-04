# Repository Guidelines

## Project Structure & Module Organization

Kyosist is a FastAPI + Supabase backend with a vanilla HTML/CSS/JavaScript frontend.

- `run.py` is the local FastAPI entry point and serves `src/public/`.
- `api/index.py` is the Vercel entry shim; keep application logic in `src/api/`.
- `src/api/index.py` defines routes, models, Supabase access, and static serving.
- `src/api/agent_service.py` contains AI agent service logic.
- `src/public/chat/` contains the chat UI (`index.html`, `main.js`, `style.css`).
- `src/public/skills/` contains the skills UI.
- `src/public/common/` contains shared UI utilities and base styles.
- `supabase/migrations/` contains database schema migrations.
- `my-playwright-project/tests/` contains Playwright tests.

## Build, Test, and Development Commands

- `python run.py`: start the local server on `http://localhost:8000`.
- `uvicorn run:app`: equivalent local ASGI server command.
- `start.bat`: Windows helper that starts the server and opens the browser.
- `ruff check .`: lint Python files.
- `ruff format --check .`: verify Python formatting.
- `ruff format .`: format Python files.
- `cd my-playwright-project && npx playwright test`: run Playwright browser tests.

Install Python dependencies with `pip install -r requirements.txt`. Install browser test dependencies from `my-playwright-project/` with `npm install`.

## Coding Style & Naming Conventions

Python uses 4-space indentation, type hints where practical, `snake_case` functions and variables, `PascalCase` Pydantic models, and `UPPER_SNAKE_CASE` constants. Private helpers use a leading underscore, for example `_insert_message()`.

JavaScript uses ES modules, `camelCase` variables/functions, `UPPER_SNAKE_CASE` constants, and `onPascalCase` event handlers such as `onWelcomeInputChange()`. CSS classes and HTML IDs use kebab-case. Keep shared frontend helpers generic in `src/public/common/`; feature-specific behavior belongs under the feature directory.

## Testing Guidelines

Run Ruff before completing Python changes. Playwright is configured with `baseURL: http://localhost:8000`, so start `python run.py` before local browser tests. Name Playwright specs `*.spec.ts` under `my-playwright-project/tests/`. Prefer tests that exercise the local Kyosist app rather than external sites.

## Commit & Pull Request Guidelines

Recent history uses concise conventional prefixes such as `fix:`, `feat:`, and `chore:`; continue that pattern and write the subject in the project language used by the change. Keep commits focused.

Pull requests should include a short summary, verification commands run, linked issues when applicable, and screenshots or screen recordings for UI changes. Note any environment or migration requirements.

## Security & Configuration Tips

Do not commit real secrets from `.env` or `.env.local`. Use `.env.example` for documented keys such as `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and AI provider keys. Avoid hardcoding deployment-specific URLs; frontend calls should use relative `/api/...` paths.
