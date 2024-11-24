from typing import Optional

from sqlalchemy import Connection, Engine, create_engine, event

from app.core.config import settings


class DBConnectionManager:
    def __init__(self, db_uri: str) -> None:
        self.base_uri: str = db_uri
        self.readonly_engine: Engine = self._create_engine(readonly=True)
        self.readwrite_engine: Engine = self._create_engine(readonly=False)
        self._register_event_listeners()

    def _create_engine(self, readonly: bool) -> Engine:
        uri = self.base_uri
        if readonly:
            uri += "&mode=ro"
        return create_engine(uri, echo=False, connect_args={"check_same_thread": False})

    def _register_event_listeners(self) -> None:
        for engine in [self.readonly_engine, self.readwrite_engine]:

            @event.listens_for(engine, "connect")
            def apply_conn_settings(
                dbapi_connection: Connection, connection_record: Optional[object]
            ) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.execute("PRAGMA busy_timeout = 5000")
                cursor.close()

    def get_engine(self, readonly: bool = True) -> Engine:
        engine = self.readonly_engine if readonly else self.readwrite_engine
        return engine


db_manager = DBConnectionManager(settings.SQLALCHEMY_DATABASE_URI)
