# SplitBill

แอปหารค่าใช้จ่ายในกลุ่ม — FastAPI + Next.js + PostgreSQL 16

## สถานะ

ขั้นตอนที่ 1: ตั้งโครงโปรเจกต์และเครื่องมือแล้ว มีเพียง API `/health` และหน้าเริ่มต้นของ Next.js
ยังไม่มี schema/migrations, seed, expense API หรือ UI ใช้งานจริง ดู PLAN.md และ CHECKLIST.md

## Prerequisites

- Python 3.12+ และ uv (backend เลือก Python 3.12 ผ่าน .python-version)
- Node.js 20.9+ และ npm (ตรวจด้วย Node.js 24)
- PostgreSQL 16 สำหรับขั้นตอนฐานข้อมูลถัดไป ยังไม่จำเป็นต่อ health test
- Windows PowerShell: ใช้ npm.cmd/npx.cmd หาก execution policy บล็อก npm.ps1

## Backend

จาก root repository:

```powershell
cd backend
uv sync --locked
Copy-Item .env.example .env
uv run fastapi dev
```

แก้ DATABASE_URL ใน backend/.env เมื่อเตรียม PostgreSQL แล้ว
CORS_ORIGINS เป็น JSON array ของ frontend origins
API: http://localhost:8000/health — ตรวจ process เท่านั้น ไม่ตรวจ database
OpenAPI: http://localhost:8000/docs

```powershell
# จาก backend/
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Frontend

```powershell
# จาก root repository
cd frontend
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

เปิด http://localhost:3000
NEXT_PUBLIC_API_BASE_URL เป็น URL สาธารณะของ API ห้ามใส่ secrets ในตัวแปร NEXT_PUBLIC_*
หน้าเริ่มต้นยังไม่ได้เรียก API; จะเชื่อมในขั้นตอน frontend

```powershell
# จาก frontend/
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

## โครงสร้างและแนวทาง

- backend/app/api: HTTP routes; core: configuration
- backend/app/services: business rules; repositories: data access (ยังเป็นโครงว่าง)
- backend/tests: pytest; ตอนนี้ตรวจ health response และ CORS headers
- frontend/src/app: Next.js App Router + TypeScript + Tailwind CSS
- uv.lock และ package-lock.json: เก็บใน Git เพื่อให้ติดตั้ง dependencies ซ้ำได้
- Config อยู่ใน environment variables และไฟล์ .env ที่ไม่เข้า Git
- PDF โจทย์ถูก ignore เฉพาะไฟล์ Developer-Take-Home-Test.pdf ที่ root

## ข้อจำกัดและขั้นตอนถัดไป

เริ่มขั้นตอนที่ 2: schema, Alembic migrations, seed, กติกาเงิน และ unit tests
จากนั้นทำ API, frontend และ integration tests ตาม PLAN.md
ยังไม่ได้ตรวจ fresh clone ทั้งระบบ และยังไม่มี migration/seed commands ให้รัน
Design decisions ที่ยังไม่ implement อยู่ใน PLAN.md; จะอัปเดตส่วนนี้เมื่อพัฒนาและตรวจแล้ว

## เวลาที่ใช้

ยังไม่ได้รับข้อมูลเวลาทำงานจริงจากผู้ทำ ต้องบันทึกและรวมเวลาจริงก่อนส่งงาน
