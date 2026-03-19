from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent

load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env", override=False)

host = os.getenv("BACKEND_HOST", "0.0.0.0")
port = int(os.getenv("BACKEND_PORT", "8000"))

uvicorn.run("app.main:app", host=host, port=port, reload=True)
