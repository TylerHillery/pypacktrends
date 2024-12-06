import sqlite3
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Connection, Engine, create_engine, event

from app.core.config import settings


class DBConnectionManager:
    def __init__(self, db_uri: str) -> None:
        self.base_uri: str = db_uri
        self.read_engine: Engine = self._create_engine(read_only=True)
        self.write_engine: Engine = self._create_engine(read_only=False)
        self._register_event_listeners()

    def _create_engine(self, read_only: bool) -> Engine:
        uri = self.base_uri
        if read_only:
            uri += "&mode=ro"
        return create_engine(uri, echo=False, connect_args={"check_same_thread": False})

    def _register_event_listeners(self) -> None:
        for engine in [self.read_engine, self.write_engine]:

            @event.listens_for(engine, "connect")
            def apply_conn_settings(
                dbapi_connection: Connection, connection_record: Optional[object]
            ) -> None:
                sqlite3.register_adapter(date, date.isoformat)
                sqlite3.register_adapter(datetime, datetime.isoformat)
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("PRAGMA busy_timeout = 5000")
                cursor.execute("pragma synchronous = normal;")
                cursor.close()

    def get_engine(self, read_only: bool = True) -> Engine:
        engine = self.read_engine if read_only else self.write_engine
        return engine


db_manager = DBConnectionManager(settings.SQLALCHEMY_DATABASE_URI)
read_engine = db_manager.get_engine(read_only=True)
write_engine = db_manager.get_engine(read_only=False)
