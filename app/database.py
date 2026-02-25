import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -------------------------------------------------
# ENV SELECTION
# -------------------------------------------------
DB_ENV = os.getenv("DB_ENV", "local")

if DB_ENV == "local":
    load_dotenv(".env.local")
else:
    load_dotenv(".env.cloud")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# -------------------------------------------------
# ENGINE CONFIG
# -------------------------------------------------
# Cloud (Aiven) needs SSL + timeouts
if DB_ENV == "cloud":
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={
            "charset": "utf8mb4",
            "connect_timeout": 10,
            "read_timeout": 10,
            "write_timeout": 10,
            "ssl": {"ca": None},
        },
    )
else:
    # Local MySQL does NOT need SSL args
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

# -------------------------------------------------
# SESSION & BASE
# -------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()

# -------------------------------------------------
# DEPENDENCY
# -------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
