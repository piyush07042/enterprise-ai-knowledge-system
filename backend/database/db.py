from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./enterprise.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_user_profile_picture_column():
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users")}

    if "profile_picture_path" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN profile_picture_path TEXT"))


def ensure_history_columns():
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("history")}

    with engine.begin() as connection:
        if "latency" not in columns:
            connection.execute(text("ALTER TABLE history ADD COLUMN latency REAL"))
        if "confidence" not in columns:
            connection.execute(text("ALTER TABLE history ADD COLUMN confidence REAL"))
        if "retrieved_docs" not in columns:
            connection.execute(text("ALTER TABLE history ADD COLUMN retrieved_docs TEXT"))

inspector = inspect(engine)

columns = [
    col["name"]
    for col in inspector.get_columns("users")
]

if "role" not in columns:
    with engine.connect() as conn:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'"
            )
        )
        conn.commit()

        print("role column added.")