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

## 10. [DEBUG] ลบ Users ทั้งหมด

> ไม่ต้อง login — ลบ users ทุกคนพร้อม cascade (settings, tasks, subjects)

```bash
curl -s -X DELETE http://localhost:8000/api/users/all \
  | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
{
    "status": "deleted",
    "count": 3
}
```

---

## 12. ดู Tasks ทั้งหมด

```bash
curl -s -b cookies.txt "http://localhost:8000/api/tasks?week_offset=0&status=active" \
  | python3 -m json.tool
```

**Query params:**
- `week_offset` — สัปดาห์ที่ต้องการ (0 = สัปดาห์นี้, 1 = สัปดาห์หน้า, -1 = สัปดาห์ที่แล้ว)
- `status` — `active` (pending+in_progress), `completed`, `all`

**ผลที่ได้ (200):**
```json
[
  {
    "id": 1,
    "title": "ทำการบ้านคณิต",
    "deadline_date": "2026-05-05",
    "difficulty": 3,
    "importance": 4,
    "comfortable": false,
    "estimated_hours": 2.5,
    "status": "pending",
    "subject_id": 1,
    "user_id": 1,
    "created_at": "2026-04-30T10:00:00",
    "updated_at": null,
    "task_slots": []
  }
]
```

---

## 11. ดู Task เดียว

```bash
curl -s -b cookies.txt http://localhost:8000/api/tasks/1 \
  | python3 -m json.tool
```

**ผลที่ได้ถ้าไม่เจอ (404):**
```json
{
    "status": "error",
    "code": 404,
    "message": "Task with id 1 not found"
}
```

---

## 12. สร้าง Task

```bash
curl -s -b cookies.txt -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "ทำการบ้านคณิต",
    "deadline_date": "2026-05-05",
    "difficulty": 3,
    "importance": 4,
    "comfortable": false,
    "estimated_hours": 2.5,
    "status": "pending",
    "subject_id": 1,
    "user_id": 1,
    "slots": [
      {
        "slot_date": "2026-05-01",
        "start_hour": 9.0,
        "hours": 1.5
      }
    ]
  }' | python3 -m json.tool
```

**ผลที่ได้ (201):** — คืน task object เดียวกับข้อ 10

---

## 13. แก้ Task

> ส่งเฉพาะ field ที่อยากเปลี่ยน (`title` หรือ `status`)

```bash
curl -s -b cookies.txt -X PATCH http://localhost:8000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }' | python3 -m json.tool
```

**status ที่ใช้ได้:** `pending`, `in_progress`, `completed`

---

## 14. ลบ Task

```bash
curl -s -b cookies.txt -X DELETE http://localhost:8000/api/tasks/1
```

**ผลที่ได้ (204):** — ไม่มี body

---

## 15. ดู Subjects ทั้งหมด

```bash
curl -s -b cookies.txt "http://localhost:8000/api/subjects?user_id=1" \
  | python3 -m json.tool
```

**ผลที่ได้ (200):**
```json
[
  {
    "id": 1,
    "name": "คณิตศาสตร์",
    "short_name": "MATH",
    "color": "#FF5733",
    "sort_order": 0,
    "user_id": 1,
    "created_at": "2026-04-30T10:00:00"
  }
]
```

---

## 16. ดู Subject เดียว

```bash
curl -s -b cookies.txt http://localhost:8000/api/subjects/1 \
  | python3 -m json.tool
```

---

## 17. สร้าง Subject

```bash
curl -s -b cookies.txt -X POST http://localhost:8000/api/subjects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mathimatics",
    "short_name": "MATH",
    "color": "#FF5733",
    "sort_order": 0,
    "user_id": 1
  }' | python3 -m json.tool
```

**ผลที่ได้ (201):** — คืน subject object เดียวกับข้อ 15

---

## 18. แก้ Subject

> ส่งเฉพาะ field ที่อยากเปลี่ยน

```bash
curl -s -b cookies.txt -X PATCH http://localhost:8000/api/subjects/1 \
  -H "Content-Type: application/json" \
  -d '{
    "color": "#00BFFF",
    "sort_order": 1
  }' | python3 -m json.tool
```

**field ที่แก้ได้:** `name`, `short_name`, `color`, `sort_order`

---

## 19. ลบ Subject

```bash
curl -s -b cookies.txt -X DELETE http://localhost:8000/api/subjects/1
```

**ผลที่ได้ (204):** — ไม่มี body

---

## สรุป Endpoints ทั้งหมด

| Method | Path | ต้อง Login | คำอธิบาย |
|--------|------|-----------|----------|
| POST | `/auth/register` |  ✓ | สมัครสมาชิก |
| POST | `/auth/login` |  ✓ | เข้าสู่ระบบ |
| POST | `/auth/logout` | ✓ | ออกจากระบบ |
| GET | `/auth/verify` | ✓ | เช็คสถานะ session |
| GET | `/api/users/me` | ✓ | ดูข้อมูลตัวเอง |
| GET | `/api/users/me/settings` | ✓ | ดู settings |
| PATCH | `/api/users/me/settings` | ✓ | แก้ settings |
| GET | `/health` |  ✓ | เช็คสถานะ server + DB |
| GET | `/ping` |  ✓ | ping |
| DELETE | `/api/users/me` | ✓ | [DEBUG] ลบ account ตัวเอง |
| GET | `/api/tasks` |  ✓ | ดู tasks (filter week/status) |
| GET | `/api/tasks/{id}` | — | ดู task เดียว |
| POST | `/api/tasks` | — | สร้าง task |
| PATCH | `/api/tasks/{id}` | — | แก้ task |
| DELETE | `/api/tasks/{id}` | — | ลบ task |
| GET | `/api/subjects?user_id=` | — | ดู subjects ของ user |
| GET | `/api/subjects/{id}` | — | ดู subject เดียว |
| POST | `/api/subjects` | — | สร้าง subject |
| PATCH | `/api/subjects/{id}` | — | แก้ subject |
| DELETE | `/api/subjects/{id}` | — | ลบ subject |
