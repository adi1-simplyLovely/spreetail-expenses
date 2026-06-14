import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure the data directory exists
os.makedirs("./data", exist_ok=True)

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/splitease.db"

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed only for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class. Each instance of it will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models to inherit from
Base = declarative_base()

# Dependency to get a DB session per request in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
