"""Basic configuration loader for MVP.

Loads environment variables (if python-dotenv installed and .env present).
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # dotenv is optional at this stage
    pass

API_KEY = os.getenv("API_KEY", "local-secret")
from dotenv import load_dotenv
import os

load_dotenv()

API_Key = os.getenv("API_KEY", "dev-key")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))
