import os
from pathlib import Path

from fastapi.templating import Jinja2Templates


class Settings:
    PROJECT_NAME: str = "pypacktrends"
    TEMPLATES = Jinja2Templates(directory="app/templates")

    @property
    def SQLITE_DB_PATH(self) -> Path:
        return Path(
            os.getenv(
                "SQLITE_DB_PATH",
                Path(__file__).parent.resolve() / "../../../data/pypacktrends.db",
            )
        ).resolve()

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if not self.SQLITE_DB_PATH.parent.exists():
            self.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not self.SQLITE_DB_PATH.exists():
            self.SQLITE_DB_PATH.touch()

        return f"sqlite:///file:{self.SQLITE_DB_PATH}?uri=true"


settings = Settings()
templates = settings.TEMPLATES
