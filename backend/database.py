import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Menggunakan SQLite lokal agar berjalan tanpa PostgreSQL
DATABASE_URL = "sqlite:///./warehouse.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Fungsi get_db yang dibutuhkan backend/main.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()