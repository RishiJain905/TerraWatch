import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PYTHON_ENV: str = os.getenv("PYTHON_ENV", "development")
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Data refresh intervals (ms)
    ADSB_REFRESH_SECONDS: int = 30
    AIS_REFRESH_SECONDS: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./terrawatch.db"


settings = Settings()
