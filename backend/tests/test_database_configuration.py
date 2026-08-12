"""Configuración del engine compatible con SQLite local y PostgreSQL."""

from sqlalchemy.engine import URL

from app.db.database import engine_options


def test_sqlite_keeps_its_driver_specific_option():
    assert engine_options("sqlite:///test.sqlite") == {
        "connect_args": {"check_same_thread": False},
    }


def test_postgresql_does_not_receive_sqlite_options():
    url = URL.create(
        "postgresql+psycopg2",
        username="example-user",
        password="example-password",
        host="pooler.example",
        port=6543,
        database="postgres",
    )
    assert engine_options(url) == {}
