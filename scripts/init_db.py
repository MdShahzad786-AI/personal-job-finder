from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jobhunter.config import database_path
from jobhunter.db import init_db

if __name__ == "__main__":
    p=database_path(); init_db(p); print(f"Database initialized: {p}")
