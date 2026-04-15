# workload_prioritizer
Python Project for 12 Group Bell's Lab

# Description
ระบบจัดลำดับความสำคัญของงาน (Task Prioritization) ที่เชื่อมต่อกับ Google Calendar

# Requirements
- Python 3.12.0
- PostgreSQL (optional, สำหรับ production)
- Google Calendar API credentials

การทำงานร่วมกันอย่างสันติ
1. clone project 
## cd <เข้าไปใน project>

2. create "venv (virtual ennvironment)" คำสั่งนี้
## python3.12 -m venv venv

3. สั่งให้ venv ทำงาน (Active)
## source venv/bin/activate

4. ติดตั้ง depencies
## pip install -r requirements.txt

5. create ".env" ขึ้นมา

6. ลอง RUN คำสั่งนี้
## uvicorn app.main:app --reload


Docker
start Containers ครั้งแรกจะ download images นานหน่อย
## docker-compose up -d

ตรวจสอบว่า Containers ทำงานอยู่
## docker-compose ps