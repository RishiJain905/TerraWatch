import os
from pathlib import Path

from dotenv import load_dotenv

# TerraWatch/.env (repo root), then cwd — fixes Docker / uvicorn cwd = backend/ where .env may not exist.
_repo_root = Path(__file__).resolve().parents[2]
load_dotenv(_repo_root / ".env")
load_dotenv()


def _optional_float(name: str) -> float | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    return float(value)


def _optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value:
        return None
    return int(value)


class Settings:
    PYTHON_ENV: str = os.getenv("PYTHON_ENV", "development")
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Data source configuration
    ADSBLOL_API_URL: str = os.getenv("ADSBLOL_API_URL", "")
    ADSBLOL_BASE_URL: str = os.getenv("ADSBLOL_BASE_URL", "https://api.adsb.lol")
    ADSBLOL_LAT: float | None = _optional_float("ADSBLOL_LAT")
    if ADSBLOL_LAT is None:
        ADSBLOL_LAT = 37.6188056
    ADSBLOL_LON: float | None = _optional_float("ADSBLOL_LON")
    if ADSBLOL_LON is None:
        ADSBLOL_LON = -122.3754167
    ADSBLOL_RADIUS_NM: int | None = _optional_int("ADSBLOL_RADIUS_NM")
    if ADSBLOL_RADIUS_NM is None:
        ADSBLOL_RADIUS_NM = 250
    AISSTREAM_API_KEY: str = os.getenv("AISSTREAM_API_KEY", "")

    # OpenSky Network OAuth2 — free registration at https://opensky-network.org/register
    # Client credentials from: https://opensky-network.org/my-opensky/account
    OPENSKY_CLIENT_ID: str = os.getenv("OPENSKY_CLIENT_ID", "")
    OPENSKY_CLIENT_SECRET: str = os.getenv("OPENSKY_CLIENT_SECRET", "")

    # Data refresh intervals (seconds)
    ADSB_REFRESH_SECONDS: int = int(os.getenv("ADSB_REFRESH_SECONDS", "120"))
    ADSBLOL_REFRESH_SECONDS: int = int(os.getenv("ADSBLOL_REFRESH_SECONDS", "120"))
    AIS_REFRESH_SECONDS: int = int(os.getenv("AIS_REFRESH_SECONDS", "60"))
    AISSTREAM_BATCH_INTERVAL_SECONDS: int = int(os.getenv("AISSTREAM_BATCH_INTERVAL_SECONDS", "30"))
    GDELT_REFRESH_SECONDS: int = int(os.getenv("GDELT_REFRESH_SECONDS", "900"))  # 15 minutes

    # Database
    DATABASE_URL: str = "sqlite:///./terrawatch.db"


settings = Settings()
