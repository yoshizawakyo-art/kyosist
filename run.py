import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from api.index import app  # noqa: E402,F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("run:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
