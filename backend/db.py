from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from backend.config import DB_URL

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    hide_parameters=True,
)


@event.listens_for(engine, "connect")
def sqlite_config(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")


SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
