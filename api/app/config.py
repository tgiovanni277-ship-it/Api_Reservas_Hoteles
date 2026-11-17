import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def required_setting(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Falta la variable obligatoria {name}. "
            "Configúrala en .env usando .env.example como referencia."
        )
    return value

API_SECRET_KEY = required_setting("API_SECRET_KEY")
API_USERNAME = required_setting("API_USERNAME")
API_PASSWORD = required_setting("API_PASSWORD")
TOKEN_HOURS = int(os.getenv("API_TOKEN_HOURS", "1"))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip() or None
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
DATABASE = Path(os.getenv("API_DB_PATH", str(ROOT_DIR / "reservas_hotel.db")))
if not DATABASE.is_absolute():
    DATABASE = ROOT_DIR / DATABASE

DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
CORS_ALLOWED_ORIGINS = tuple(
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
)
