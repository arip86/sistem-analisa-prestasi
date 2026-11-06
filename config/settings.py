from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def _secret(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key)
    if value not in (None, ""):
        return value
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


def _bool_secret(key: str, default: bool = False) -> bool:
    value = _secret(key)
    if value in (None, ""):
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


DATABASE_URL = _secret("DATABASE_URL", "") or ""
DB_SCHEMA = (_secret("DB_SCHEMA", "prestasi") or "prestasi").strip()
APP_ENV = _secret("APP_ENV", "development") or "development"
MAX_UPLOAD_MB = int(_secret("MAX_UPLOAD_MB", "25") or 25)
PUBLIC_READ_ONLY = _bool_secret("PUBLIC_READ_ONLY", APP_ENV == "production")
ANONYMIZATION_SALT = _secret("ANONYMIZATION_SALT", "") or ""

APP_NAME = "SAPM"
APP_LONG_NAME = "Sistem Analisis Prestasi Mahasiswa"
APP_TAGLINE = "Pengelolaan, eksplorasi, dan analisis data prestasi mahasiswa"
APP_VERSION = "1.0.0"

EXCEL_SOURCE_FILE = BASE_DIR / "2025-1.xlsx"
ASSETS_DIR = BASE_DIR / "assets"
STYLE_FILE = ASSETS_DIR / "style.css"


def database_url() -> str:
    return DATABASE_URL


def is_configured() -> bool:
    return bool(DATABASE_URL)
