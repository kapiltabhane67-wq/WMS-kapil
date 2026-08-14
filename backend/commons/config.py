from pathlib import Path
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "Whitfield WMS")
    database_path: Path = Path(os.getenv("DATABASE_PATH", "./data/wms_client_ready.sqlite3"))


settings = Settings()
