"""Connexion SQLAlchemy et session par requête."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Crée le dossier data/ si la base SQLite est locale (ex. sqlite:///./data/app.db)
    db_path = settings.database_url.split("///")[-1]
    if db_path not in (":memory:", ""):
        Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
