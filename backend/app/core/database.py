from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # ตรวจสอบ connection ก่อนใช้งาน
    echo=settings.DEBUG   # แสดง SQL queries ถ้า DEBUG=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection():
    """ทดสอบการเชื่อมต่อ database"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✅ Database connection successful!")
        return True
    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(f"❌ {error_msg}")
        from app.core.exceptions import DatabaseError
        raise DatabaseError(error_msg)

def create_tables():
    """สร้างตารางทั้งหมดใน database"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {str(e)}")
