# SplitBill

แอปหารค่าใช้จ่ายในกลุ่ม — FastAPI + Next.js + PostgreSQL 16

## สถานะ

ขั้นตอนที่ 1: ตั้งโปรเจกต์ครบ พร้อม PostgreSQL 16, API `/health` และ `/ready`, equal split service และหน้าเริ่มต้นของ Next.js
Database และ seed เสร็จแล้ว: มี schema 5 ตาราง, Alembic migration และ seed แบบรันซ้ำได้ ยังไม่มี expense API หรือ UI ใช้งานจริง ดู PLAN.md และ CHECKLIST.md

## Prerequisites

- Python 3.12+ และ uv (backend เลือก Python 3.12 ผ่าน .python-version)
- Node.js 20.9+ และ npm (ตรวจด้วย Node.js 24)
- Docker Desktop ที่เปิด engine แล้ว สำหรับ PostgreSQL 16; unit tests ไม่ต้องใช้ database
- Windows PowerShell: ใช้ npm.cmd/npx.cmd หาก execution policy บล็อก npm.ps1

## PostgreSQL 16 (local development)

จาก root repository คัดลอก backend/.env.example เป็น backend/.env หากยังไม่มี
ตั้ง POSTGRES_PASSWORD และส่วนรหัสผ่านใน DATABASE_URL ให้ตรงกันก่อนเปิดฐานข้อมูล
ใช้รหัสผ่านสำหรับ local development เท่านั้น ห้าม commit .env

```powershell
docker compose --env-file backend/.env up -d --wait db
docker compose --env-file backend/.env exec db postgres --version
```

Database เปิดเฉพาะ localhost:55432 และเก็บข้อมูลใน named volume
หยุดโดยใช้ `docker compose --env-file backend/.env stop db` ซึ่งยังคงข้อมูลไว้
Compose ชุดนี้เปิดเฉพาะฐานข้อมูล; optional containerisation ของ API ยังไม่ได้ทำ
ไม่มีการสร้าง schema อัตโนมัติที่ API startup ให้รัน Alembic ตามด้านล่าง

## Backend

จาก root repository:

```powershell
cd backend
uv sync --locked
# คัดลอกเฉพาะเมื่อยังไม่มี .env (ห้ามทับ config เดิม)
if (!(Test-Path .env)) { Copy-Item .env.example .env }
uv run alembic upgrade head
uv run python -m app.seed
uv run fastapi dev
```

แก้ DATABASE_URL ใน backend/.env ให้ตรงกับ PostgreSQL ที่ตั้งไว้
CORS_ORIGINS เป็น JSON array ของ frontend origins
API: http://localhost:8000/health — ตรวจ process เท่านั้น ไม่ตรวจ database
Readiness: http://localhost:8000/ready — ตรวจ database connection; ไม่พร้อมคืน 503
OpenAPI: http://localhost:8000/docs

```powershell
# จาก backend/
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Schema และ seed

| Table | หน้าที่และข้อบังคับสำคัญ |
| --- | --- |
| users | username เป็น primary key ใช้ระบุ X-User ใน API ขั้นถัดไป |
| groups | integer identity ID และชื่อกลุ่ม |
| memberships | primary key (group_id, username); สมาชิกซ้ำในกลุ่มไม่ได้ |
| expenses | NUMERIC(12,2), payer membership FK, created_at แบบ timezone, is_deleted |
| expense_shares | NUMERIC(12,2), member membership FK, expense/group FK และ position |

- จำนวนเงินใช้ Decimal; expense ต้องมากกว่า 0 ส่วน share อนุญาต 0 แต่ห้ามติดลบ
- Unique (group_id, idempotency_key) ป้องกันการ insert ซ้ำแม้เกิดพร้อมกัน รวมรายการ soft delete
- API ขั้นถัดไปต้องจัดการ unique conflict ให้คืน expense เดิม; ตอนนี้ทดสอบเฉพาะข้อบังคับฐานข้อมูล
- Foreign keys ป้องกัน payer/ผู้ร่วมแบ่งนอกกลุ่ม และ share ที่อ้าง expense คนละกลุ่ม
- position เก็บลำดับสมาชิกที่ใช้แจกเศษ; unique ต่อ expense เพื่อไม่ให้ลำดับชนกัน
- Index รองรับการหากลุ่มของผู้ใช้และรายจ่ายตาม group/created_at/id
- Soft delete ใช้ is_deleted เก็บ record เดิม; การตัดออกจาก balances จะ implement ใน service/API
- NUMERIC(12,2) อาจปัด input ที่ทศนิยมเกินเอง จึงต้อง validate ก่อนบันทึก; ห้ามใช้ฐานข้อมูลแทน input validation
- ผลรวม shares เท่ากับ amount และ zero-sum balances จะตรวจใน business logic ขั้นถัดไป

Seed: alice, bob, carol, dan; group 1 Chiang Mai trip (alice, bob, carol); group 2 Office lunch (bob, dan)
`uv run python -m app.seed` ใช้ transaction, ON CONFLICT DO NOTHING และ advisory lock
เพิ่มเฉพาะข้อมูลที่ขาด ไม่ลบรายจ่ายหรือทับชื่อกลุ่มเดิม; หาก ID ของ seed ชนกลุ่มชื่ออื่นจะ fail และ rollback
ปรับ sequence ของ group ID ให้การสร้างกลุ่มใหม่ไม่ชน ID ที่ seed ไว้

ตรวจว่า migrations ตรง models โดยใช้ `uv run alembic check` จาก backend/
การ downgrade ใช้เพื่อพัฒนา/ทดสอบเท่านั้น เพราะลบตารางและข้อมูลใน migration นั้น

## PostgreSQL integration tests

จาก backend/ หลังเปิด PostgreSQL แล้ว:

```powershell
$env:RUN_DB_TESTS="1"
uv run pytest
Remove-Item Env:RUN_DB_TESTS
```

ใช้ DATABASE_URL จาก backend/.env เป็น connection สำหรับสร้างฐานข้อมูลชั่วคราวชื่อ splitbill_test_<random>
บัญชีทดสอบต้องมีสิทธิ์ CREATE DATABASE และลบ database ที่ตนสร้าง (บัญชีใน local Compose มีสิทธิ์นี้)
เทสต์ migrate จากฐานข้อมูลว่าง, upgrade ซ้ำ, seed ซ้ำ, constraints, concurrent insert และ downgrade/upgrade
ข้อมูลทดสอบอยู่เฉพาะฐานข้อมูลชั่วคราวและลบทิ้งหลังจบ ไม่ downgrade หรือล้างฐานข้อมูลพัฒนา
`uv run pytest` แบบไม่ตั้ง RUN_DB_TESTS จะรัน unit tests และ skip integration tests ชุดนี้

## Frontend

```powershell
# จาก root repository
cd frontend
npm.cmd ci
# คัดลอกเฉพาะเมื่อยังไม่มี .env (ห้ามทับ config เดิม)
if (!(Test-Path .env)) { Copy-Item .env.example .env }.local
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
- backend/app/services: กติกาเงินแบบ pure functions; repositories: SQL สำหรับ database readiness
- backend/tests: pytest; ตรวจ health/CORS, การหารพร้อมเศษ และ validation ของจำนวนเงิน
- frontend/src/app: Next.js App Router + TypeScript + Tailwind CSS
- uv.lock และ package-lock.json: เก็บใน Git เพื่อให้ติดตั้ง dependencies ซ้ำได้
- Config อยู่ใน environment variables และไฟล์ .env ที่ไม่เข้า Git
- PDF โจทย์ถูก ignore เฉพาะไฟล์ Developer-Take-Home-Test.pdf ที่ root

## ข้อจำกัดและขั้นตอนถัดไป

ทำ schema, migrations และ seed แล้ว; ขั้นถัดไปคือ exact split, balances และ API ตาม PLAN.md
จากนั้นทำ API, frontend และ integration tests ตาม PLAN.md
ตรวจ migration บนฐานข้อมูลว่างผ่าน integration tests แล้ว แต่ยังไม่ได้ตรวจ fresh clone ทั้งระบบ
Design decisions ที่ยังไม่ implement อยู่ใน PLAN.md; จะอัปเดตส่วนนี้เมื่อพัฒนาและตรวจแล้ว

## เวลาที่ใช้

ยังไม่ได้รับข้อมูลเวลาทำงานจริงจากผู้ทำ ต้องบันทึกและรวมเวลาจริงก่อนส่งงาน
