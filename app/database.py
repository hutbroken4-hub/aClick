from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./aclick.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def init_db() -> None:
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_demo_data
    seed_demo_data()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
