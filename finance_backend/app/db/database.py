from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Usa a URL construída dinamicamente ou a URL direta
database_url = settings.get_database_url()

engine = create_engine(
    database_url,
    pool_pre_ping=True, 
    pool_recycle=300,   
    echo=settings.debug 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()