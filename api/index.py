import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Vercel imports this shim as api.index. Alias the real package before loading the
# app so imports inside src/api (for example api.task_api) do not resolve back to
# this shim package.
from src import api as src_api  # noqa: E402

sys.modules["api"] = src_api

from src.api.index import app  # noqa: E402,F401
