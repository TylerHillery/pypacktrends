from pathlib import Path
from typing import Literal

from fastapi.templating import Jinja2Templates
from pydantic import HttpUrl, computed_field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "pypacktrends"
    TEMPLATES: Jinja2Templates = Jinja2Templates(directory="app/templates")
    ENVIRONMENT: Literal["dev", "ci", "prod"] = "dev"
    SENTRY_DSN: HttpUrl | None = None
    SQLITE_DB_PATH: Path = (
        Path(__file__).parent.resolve() / "../../../data/pypacktrends.db"
    )

    @field_validator("SENTRY_DSN", mode="before")
    @classmethod
    def validate_sentry_dsn(cls, v: str | None) -> str | None:
        if not v or v.strip() == "":
            return None
        return v

    @computed_field  # type: ignore
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if not self.SQLITE_DB_PATH.parent.exists():
            self.SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        if not self.SQLITE_DB_PATH.exists():
            self.SQLITE_DB_PATH.touch()

        return f"sqlite:///file:{self.SQLITE_DB_PATH}?uri=true"


settings = Settings()
templates = settings.TEMPLATES
