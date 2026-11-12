from pathlib import Path
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

def make_engine(db_url: str | None = None):
    url = db_url or os.getenv('PRICEWATCH_DB_URL') or f"sqlite:///{Path(__file__).resolve().parents[1] / 'pricewatch.db'}"
    kwargs = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite') else {}
    return create_engine(url, **kwargs)

def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
