import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PYTHON_ENV: str = os.getenv("PYTHON_ENV", "development")
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Data source configuration
    ADSBLOL_API_URL: str = os.getenv("ADSBLOL_API_URL", "https://api.adsb.lol/aircraft/json")
    AIS_FRIENDS_API_KEY: str = os.getenv("AIS_FRIENDS_API_KEY", "")

    # Data refresh intervals (seconds)
    ADSB_REFRESH_SECONDS: int = int(os.getenv("ADSB_REFRESH_SECONDS", "30"))
    ADSBLOL_REFRESH_SECONDS: int = int(os.getenv("ADSBLOL_REFRESH_SECONDS", "30"))
    AIS_REFRESH_SECONDS: int = int(os.getenv("AIS_REFRESH_SECONDS", "60"))
    AIS_FRIENDS_REFRESH_SECONDS: int = int(os.getenv("AIS_FRIENDS_REFRESH_SECONDS", "60"))

    # Database
    DATABASE_URL: str = "sqlite:///./terrawatch.db"


settings = Settings()
