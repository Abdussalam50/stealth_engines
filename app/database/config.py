import os
from sqlalchemy import create_all, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Mengambil URL dari Railway, jika tidak ada (di lokal), pakai SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Perbaikan kecil untuk database postgres di Railway (SQLAlchemy butuh postgresql:// bukan postgres://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
else:
    # Default untuk lokal (laptop)
    engine = create_engine("sqlite:///./stealth.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()