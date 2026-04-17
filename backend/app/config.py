import os
from pathlib import Path

from dotenv import load_dotenv

# TerraWatch/.env (repo root), then cwd — fixes Docker / uvicorn cwd = backend/ where .env may not exist.
_repo_root = Path(__file__).resolve().parents[2]
load_dotenv(_repo_root / ".env")
load_dotenv()


class Settings:
    PYTHON_ENV: str = os.getenv("PYTHON_ENV", "development")
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Data source configuration
    ADSBLOL_API_URL: str = os.getenv("ADSBLOL_API_URL", "https://api.adsb.lol/aircraft/json")
    AISSTREAM_API_KEY: str = os.getenv("AISSTREAM_API_KEY", "")

    # OpenSky Network OAuth2 — free registration at https://opensky-network.org/register
    # Client credentials from: https://opensky-network.org/my-opensky/account
    OPENSKY_CLIENT_ID: str = os.getenv("OPENSKY_CLIENT_ID", "")
    OPENSKY_CLIENT_SECRET: str = os.getenv("OPENSKY_CLIENT_SECRET", "")

    # Data refresh intervals (seconds)
    ADSB_REFRESH_SECONDS: int = int(os.getenv("ADSB_REFRESH_SECONDS", "30"))
    ADSBLOL_REFRESH_SECONDS: int = int(os.getenv("ADSBLOL_REFRESH_SECONDS", "30"))
    AIS_REFRESH_SECONDS: int = int(os.getenv("AIS_REFRESH_SECONDS", "60"))
    AISSTREAM_BATCH_INTERVAL_SECONDS: int = int(os.getenv("AISSTREAM_BATCH_INTERVAL_SECONDS", "30"))
    GDELT_REFRESH_SECONDS: int = int(os.getenv("GDELT_REFRESH_SECONDS", "900"))  # 15 minutes

    # Database
    DATABASE_URL: str = "sqlite:///./terrawatch.db"


settings = Settings()
