import os

from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import declarative_base, sessionmaker


DEFAULT_DATABASE_URL = "sqlite:///../database/futbol_entrenamiento.sqlite"
DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL


def engine_options(database_url: str | URL) -> dict:
    """Devuelve únicamente opciones compatibles con el driver configurado."""
    if make_url(database_url).get_backend_name() == "sqlite":
        return {"connect_args": {"check_same_thread": False}}
    return {}

engine = create_engine(
    DATABASE_URL,
    **engine_options(DATABASE_URL),
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """Activa la integridad referencial en cada conexión SQLite."""
    if dbapi_connection.__class__.__module__ == "sqlite3":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
