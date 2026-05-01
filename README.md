# Workload Prioritizer

ระบบจัดลำดับความสำคัญของงานที่เชื่อมต่อกับ Google Calendar พัฒนาด้วย FastAPI, PostgreSQL และ Next.js

## สารบัญ

- [สถาปัตยกรรมระบบ](#สถาปัตยกรรมระบบ)
- [ความต้องการของระบบ](#ความต้องการของระบบ)
- [การตั้งค่า Google OAuth](#การตั้งค่า-google-oauth)
- [การรันบนเครื่องด้วย Docker](#การรันบนเครื่องด้วย-docker)
- [การรัน Frontend](#การรัน-frontend)
- [ตัวแปร Environment](#ตัวแปร-environment)
- [คำสั่งที่ใช้บ่อย](#คำสั่งที่ใช้บ่อย)
- [การแก้ปัญหาเบื้องต้น](#การแก้ปัญหาเบื้องต้น)

---

## สถาปัตยกรรมระบบ

| Service   | เทคโนโลยี            | Port |
|-----------|----------------------|------|
| Backend   | FastAPI + Uvicorn    | 8000 |
| Database  | PostgreSQL 15        | 5432 |
| Frontend  | Next.js 16 + React   | 3000 |

Docker Compose จัดการ backend และ database ส่วน frontend รันแยกนอก Docker ในระหว่างการพัฒนา

---

## ความต้องการของระบบ

- [Docker](https://docs.docker.com/get-docker/) เวอร์ชัน 24 ขึ้นไป
- [Docker Compose](https://docs.docker.com/compose/install/) เวอร์ชัน 2 ขึ้นไป
- [Node.js](https://nodejs.org/) เวอร์ชัน 20 ขึ้นไป (สำหรับ frontend)
- Google Cloud project ที่เปิดใช้งาน Calendar API แล้ว

---

## การตั้งค่า Google OAuth

แอปพลิเคชันต้องใช้ Google OAuth 2.0 credentials เพื่อเข้าถึง Google Calendar

1. เปิด [Google Cloud Console](https://console.cloud.google.com/)
2. สร้าง project ใหม่หรือเลือก project ที่มีอยู่
3. ไปที่ **APIs & Services > Library** แล้วเปิดใช้งาน **Google Calendar API**
4. ไปที่ **APIs & Services > Credentials** แล้วคลิก **Create Credentials > OAuth 2.0 Client IDs**
5. เลือกประเภทแอปพลิเคชันเป็น **Web application**
6. เพิ่ม URI ต่อไปนี้ใน **Authorized redirect URIs**:
   ```
   http://localhost:8000/auth/google/callback
   ```
7. คัดลอก **Client ID** และ **Client Secret** ที่ได้ไปใส่ในไฟล์ `.env` (ดูหัวข้อถัดไป)

---

## การรันบนเครื่องด้วย Docker

### 1. Clone repository

```bash
git clone <repository-url>
cd workload_prioritizer
```

### 2. ตั้งค่า Environment Variables

```bash
cp backend/.env.example backend/.env
```

เปิดไฟล์ `backend/.env` แล้วกรอกค่าที่จำเป็น:

```env
DATABASE_URL=postgresql://postgres:postgres123@db:5432/workload_db
APP_NAME=Workload Prioritizer
DEBUG=True
SECRET_KEY=<สร้าง secret key แบบสุ่ม>
GOOGLE_CLIENT_ID=<client id จาก Google Cloud Console>
GOOGLE_CLIENT_SECRET=<client secret จาก Google Cloud Console>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
HOST=0.0.0.0
PORT=8000
```

> **หมายเหตุ:** เมื่อรันใน Docker ให้ใช้ `db` เป็น hostname ใน `DATABASE_URL` ไม่ใช่ `localhost` เพราะ `db` คือชื่อ service ใน Docker Compose

สร้าง `SECRET_KEY` แบบสุ่มด้วยคำสั่ง:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. เริ่มต้น Services

```bash
docker compose up -d
```

คำสั่งนี้จะเริ่มต้น container `backend` และ `db` การรันครั้งแรกจะใช้เวลาสักครู่เนื่องจากต้องดาวน์โหลด image และ build

### 4. ตรวจสอบว่า Services ทำงานปกติ

```bash
docker compose ps
```

ผลลัพธ์ที่ควรได้:

```
NAME                STATUS
workload_backend    Up (healthy)
workload_db         Up (healthy)
```

### 5. ทดสอบ API

```bash
curl http://localhost:8000/ping
```

เอกสาร API สามารถเข้าถึงได้ที่:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## การรัน Frontend

Frontend ไม่ได้อยู่ใน Docker Compose จึงต้องรันแยกต่างหาก

### 1. ติดตั้ง Dependencies

```bash
cd frontend
npm install
```

### 2. เริ่มต้น Development Server

```bash
npm run dev
```

เข้าถึง frontend ได้ที่ [http://localhost:3000](http://localhost:3000)

---

## ตัวแปร Environment

| ตัวแปร                  | คำอธิบาย                                              | ตัวอย่าง                                                   |
|-------------------------|-------------------------------------------------------|------------------------------------------------------------|
| `DATABASE_URL`          | Connection string สำหรับ PostgreSQL                   | `postgresql://postgres:postgres123@db:5432/workload_db`    |
| `SECRET_KEY`            | Secret key สำหรับการ sign JWT                         | สตริง hex ขนาด 32 bytes                                    |
| `APP_NAME`              | ชื่อแอปพลิเคชัน                                        | `Workload Prioritizer`                                     |
| `DEBUG`                 | เปิด/ปิด debug mode                                   | `True` / `False`                                           |
| `GOOGLE_CLIENT_ID`      | Google OAuth 2.0 Client ID                            | ได้จาก Google Cloud Console                                |
| `GOOGLE_CLIENT_SECRET`  | Google OAuth 2.0 Client Secret                        | ได้จาก Google Cloud Console                                |
| `GOOGLE_REDIRECT_URI`   | Callback URL ที่ลงทะเบียนใน Google Console            | `http://localhost:8000/auth/google/callback`               |
| `HOST`                  | Host ที่ Uvicorn รับการเชื่อมต่อ                       | `0.0.0.0`                                                  |
| `PORT`                  | Port ที่ Uvicorn รับการเชื่อมต่อ                       | `8000`                                                     |

---

## คำสั่งที่ใช้บ่อย

| การกระทำ                          | คำสั่ง                                                   |
|-----------------------------------|----------------------------------------------------------|
| เริ่มต้น services ทั้งหมด          | `docker compose up -d`                                   |
| หยุด services ทั้งหมด              | `docker compose down`                                    |
| หยุดและลบข้อมูลใน volume           | `docker compose down -v`                                 |
| ดู log ของ backend                 | `docker compose logs -f backend`                         |
| ดู log ของ database                | `docker compose logs -f db`                              |
| Build backend image ใหม่           | `docker compose up -d --build backend`                   |
| เปิด shell ใน backend container    | `docker compose exec backend bash`                       |
| เชื่อมต่อ PostgreSQL               | `docker compose exec db psql -U postgres -d workload_db` |
| Restart service เดี่ยว             | `docker compose restart backend`                         |

---

## การแก้ปัญหาเบื้องต้น

**Backend เริ่มไม่ติดและ error เรื่อง database connection**

ตรวจสอบว่า `DATABASE_URL` ใน `backend/.env` ใช้ `db` เป็น hostname ไม่ใช่ `localhost` เพราะภายใน Docker network จะอ้างอิงด้วยชื่อ service

**Port ถูกใช้งานอยู่แล้ว**

ตรวจสอบว่ามี process อื่นใช้ port `8000` หรือ `5432` อยู่หรือไม่:

```bash
lsof -i :8000
lsof -i :5432
```

หยุด process นั้นก่อนแล้วค่อยเริ่ม Docker Compose ใหม่

**แก้ไขโค้ดแล้วไม่มีการเปลี่ยนแปลง**

โฟลเดอร์ `./backend` ถูก mount เป็น volume และ Uvicorn รันด้วย `--reload` ดังนั้นการแก้ไขโค้ดจะมีผลทันที แต่หากเพิ่ม dependency ใน `requirements.txt` ต้อง build image ใหม่:

```bash
docker compose up -d --build backend
```

**Google OAuth error: redirect URI mismatch**

ตรวจสอบว่า redirect URI ที่ตั้งค่าใน Google Cloud Console ตรงกับ `GOOGLE_REDIRECT_URI` ใน `backend/.env` ทุกตัวอักษร รวมถึง protocol และ path
