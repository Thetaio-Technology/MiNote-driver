from __future__ import annotations

import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHROMEDRIVER_EXE = PROJECT_ROOT / "bin" / "chromedriver.exe"
CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHROME_USER_DATA_DIR = PROJECT_ROOT / "chrome_profile"
TARGET_URL = "https://i.mi.com/note/#/"
REMOTE_DEBUGGING_PORT = 9222

MI_API_BASE = "https://i.mi.com"
CHROME_PROFILE_DIR = PROJECT_ROOT / "chrome_profile"

_DRIVER_MODE: str | None = None


def get_driver_mode() -> str:
    global _DRIVER_MODE
    if _DRIVER_MODE is not None:
        return _DRIVER_MODE
    config_path = PROJECT_ROOT / "minote.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        _DRIVER_MODE = data.get("driver", {}).get("mode", "http")
    else:
        _DRIVER_MODE = "http"
    if _DRIVER_MODE not in ("http", "selenium"):
        raise ValueError(f"Unknown driver mode: {_DRIVER_MODE}. Use 'http' or 'selenium'.")
    return _DRIVER_MODE
