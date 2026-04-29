# Pete's Auth Integration — API Test Guide

> ทดสอบด้วย curl ทั้งหมด  
> Base URL: `http://localhost:8000`  
> Cookie จะถูกเก็บไว้ในไฟล์ `cookies.txt` อัตโนมัติ

---

## 1. สมัครสมาชิก

```bash
curl -s -c cookies.txt -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pete@example.com",
    "password": "secret123",
    "display_name": "Pete"
  }' | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "id": 1,
    "email": "pete@example.com",
    "display_name": "Pete",
    "created_at": "2026-04-30T10:00:00"
}
```

**กฎของ password:**
- ขั้นต่ำ 6 ตัวอักษร
- สูงสุด 72 bytes (ระวัง emoji/ภาษาไทย)

---

## 2. เข้าสู่ระบบ

```bash
curl -s -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pete@example.com",
    "password": "secret123"
  }' | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "id": 1,
    "email": "pete@example.com",
    "display_name": "Pete",
    "created_at": "2026-04-30T10:00:00"
}
```

> Cookie `access_token` จะถูกบันทึกใน `cookies.txt` เพื่อใช้ใน request ถัดไป

---

## 3. ตรวจสอบว่า Login อยู่มั้ย

```bash
curl -s -b cookies.txt http://localhost:8000/auth/verify \
  | python3 -m json.tool
```

**ผลที่ได้ถ้า login อยู่ (200):**
```json
{
    "id": 1,
    "email": "pete@example.com",
    "display_name": "Pete",
    "created_at": "2026-04-30T10:00:00"
}
```

**ผลที่ได้ถ้าไม่ได้ login (401):**
```json
{
    "status": "error",
    "code": 401,
    "message": "Not authenticated"
}
```

---

## 4. ดูข้อมูลตัวเอง

```bash
curl -s -b cookies.txt http://localhost:8000/api/users/me \
  | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "id": 1,
    "email": "pete@example.com",
    "display_name": "Pete",
    "created_at": "2026-04-30T10:00:00"
}
```

---

## 5. ดู Settings ของตัวเอง

```bash
curl -s -b cookies.txt http://localhost:8000/api/users/me/settings \
  | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "chart_type": "bar",
    "capacity": 10,
    "density": "normal"
}
```

---

## 6. แก้ Settings

> ส่งเฉพาะ field ที่อยากเปลี่ยน ไม่ต้องส่งทั้งหมด

```bash
curl -s -b cookies.txt -X PATCH http://localhost:8000/api/users/me/settings \
  -H "Content-Type: application/json" \
  -d '{
    "chart_type": "line",
    "capacity": 20
  }' | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "chart_type": "line",
    "capacity": 20,
    "density": "normal"
}
```

---

## 7. ออกจากระบบ

```bash
curl -s -c cookies.txt -b cookies.txt -X POST http://localhost:8000/auth/logout \
  | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "status": "logged out"
}
```

---

## 8. System Endpoints

### Health Check — เช็คว่า server และ DB ทำงานอยู่มั้ย

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

**ผลที่ได้ถ้าปกติ (200):**
```json
{
    "status": "healthy",
    "checks": {
        "database": {
            "status": "healthy",
            "latency_ms": 3.21
        }
    }
}
```

**ผลที่ได้ถ้า DB มีปัญหา (503):**
```json
{
    "status": "degraded",
    "checks": {
        "database": {
            "status": "unhealthy",
            "latency_ms": 0.12,
            "error": "..."
        }
    }
}
```

### Ping

```bash
curl -s http://localhost:8000/ping | python3 -m json.tool
```

```json
{
    "status": "success",
    "detail": "pong!"
}
```

---

---

## 9. [DEBUG] ลบ account ตัวเอง

> ใช้สำหรับ debug เท่านั้น — ลบ user + settings + logout ในครั้งเดียว

```bash
curl -s -c cookies.txt -b cookies.txt -X DELETE http://localhost:8000/api/users/me \
  | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "status": "deleted",
    "email": "pete@example.com"
}
```

---

## สรุป Endpoints ทั้งหมด

| Method | Path | ต้อง Login | คำอธิบาย |
|--------|------|-----------|----------|
| POST | `/auth/register` | — | สมัครสมาชิก |
| POST | `/auth/login` | — | เข้าสู่ระบบ |
| POST | `/auth/logout` | ✓ | ออกจากระบบ |
| GET | `/auth/verify` | ✓ | เช็คสถานะ session |
| GET | `/api/users/me` | ✓ | ดูข้อมูลตัวเอง |
| GET | `/api/users/me/settings` | ✓ | ดู settings |
| PATCH | `/api/users/me/settings` | ✓ | แก้ settings |
| GET | `/health` | — | เช็คสถานะ server + DB |
| GET | `/ping` | — | ping |
| DELETE | `/api/users/me` | ✓ | [DEBUG] ลบ account ตัวเอง |
