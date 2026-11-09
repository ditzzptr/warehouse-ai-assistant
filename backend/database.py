import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default: SQLite lokal (file warehouse.db di root proyek).
# Untuk data yang permanen saat di-deploy, isi DATABASE_URL (mis. dari Neon/Supabase)
# lewat Streamlit Secrets atau environment variable.
_DEFAULT_SQLITE = Path(__file__).resolve().parent.parent / "warehouse.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_SQLITE}")

# Neon/Supabase biasanya memberi URL "postgresql://..." atau "postgres://...".
# Driver yang terpasang adalah psycopg v3, jadi skemanya perlu disesuaikan.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Fungsi get_db yang dibutuhkan backend/main.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
