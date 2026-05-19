"""Configuration loading via python-dotenv."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env(dotenv_path: str | None = None) -> None:
    """Load .env from project root or supplied path. Idempotent."""
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
        return
    root = Path(__file__).resolve().parents[2]
    env_file = root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)


def get(key: str, default: str | None = None) -> str | None:
    load_env()
    return os.environ.get(key, default)


def get_int(key: str, default: int) -> int:
    raw = get(key)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default
