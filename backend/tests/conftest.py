from __future__ import annotations

import sys
from pathlib import Path


# Ensure `import app...` works regardless of where pytest is launched from.
BACKEND_DIR = Path(__file__).resolve().parents[1]
backend_path = str(BACKEND_DIR)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
