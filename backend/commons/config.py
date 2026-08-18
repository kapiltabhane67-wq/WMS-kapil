from pathlib import Path
from pydantic import BaseModel
import os


def env_csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def default_database_path() -> Path:
    if os.getenv("VERCEL"):
        return Path("/tmp/wms_client_ready.sqlite3")
    return Path("./data/wms_client_ready.sqlite3")


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Whitfield WMS")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(default_database_path())))
    allowed_origins: list[str] = env_csv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:3001,http://localhost:3001",
    )
    allowed_origin_regex: str | None = os.getenv(
        "ALLOWED_ORIGIN_REGEX",
        r"^https://[a-z0-9-]+\.onrender\.com$",
    )


settings = Settings()
