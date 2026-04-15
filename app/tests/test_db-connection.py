import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    # เชื่อมต่อ database
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    # ทดสอบ query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"✅ PostgreSQL version: {version[0]}")
    
    # ทดสอบสร้าง table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100)
        );
    """)
    conn.commit()
    print("✅ Table created successfully!")
    
    # ปิดการเชื่อมต่อ
    cursor.close()
    conn.close()
    
    print("✅ Database connection successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
