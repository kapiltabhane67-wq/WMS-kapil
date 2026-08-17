from pathlib import Path
from pydantic import BaseModel
import os


def default_database_path() -> Path:
    if os.getenv("VERCEL"):
        return Path("/tmp/wms_client_ready.sqlite3")
    return Path("./data/wms_client_ready.sqlite3")


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Whitfield WMS")
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(default_database_path())))
    allowed_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://127.0.0.1:3001,http://localhost:3001",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
