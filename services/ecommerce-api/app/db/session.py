from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

database_url = settings.database_url
if "charset=" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}charset=utf8mb4"

engine = create_engine(
    database_url,
    isolation_level="READ COMMITTED",
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

