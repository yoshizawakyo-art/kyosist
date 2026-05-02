import sys
from pathlib import Path

# Add src to the Python import path so we can reuse the app implementation there.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from api.index import app  # noqa: E402,F401
