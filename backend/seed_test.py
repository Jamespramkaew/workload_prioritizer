"""
สร้าง test user ใน DB และ generate JWT token สำหรับทดสอบ GET /api/users/me
รันใน Docker: docker exec -it workload_backend python seed_test.py
"""
import os
import jwt
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models import *  # ensure all models are loaded

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/workload_db")
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Insert test user (skip ถ้ามีอยู่แล้ว)
user = db.query(User).filter(User.email == "test@dev.local").first()
if not user:
    user = User(
        email="test@dev.local",
        password="hashed_password_placeholder",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created user id={user.id}")
else:
    print(f"User already exists id={user.id}")

# Generate JWT
token = jwt.encode({"sub": str(user.id)}, SECRET_KEY, algorithm="HS256")

print(f"\nJWT Token:\n{token}")
print(f"\nTest command:")
print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/api/users/me')

db.close()
