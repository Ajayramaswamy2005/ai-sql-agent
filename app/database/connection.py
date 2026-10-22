from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def execute_sql(sql: str, params: dict | None = None) -> tuple[list[str], list[list]]:
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return columns, rows


def validate_sql_dry_run(sql: str) -> str | None:
    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {sql}"))
        return None
    except Exception as e:
        return str(e)
