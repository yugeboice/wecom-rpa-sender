from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.models.task_orm import Base

# 确保数据目录存在
_db_url_prefix = "sqlite:///"
if settings.database_url.startswith(_db_url_prefix):
    _db_path = Path(settings.database_url[len(_db_url_prefix):])
    _db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
