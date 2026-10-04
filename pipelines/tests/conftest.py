import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("SILVER_PSEUDONYMIZE_SALT", "test_secret_pii_salt_nd13_pytest_2026")

