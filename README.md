# SplitBill

แอปหารค่าใช้จ่ายในกลุ่ม — FastAPI + Next.js + PostgreSQL 16

## สถานะ

Project setup, Database/seed, Backend API, Business rules และ Frontend เสร็จแล้ว
ตรวจจาก fresh clone แล้ว: Backend 70 กรณี, Frontend unit tests 4 กรณีและ browser tests 8 กรณีผ่าน รวม desktop/mobile ดู FINAL_REVIEW.md
ติดตามงานที่เหลือใน PLAN.md และ CHECKLIST.md

## Prerequisites

- Python 3.12+ และ uv (backend เลือก Python 3.12 ผ่าน .python-version)
- Node.js 24+ และ npm สำหรับ frontend รวม unit test runner (ตรวจด้วย Node.js 24)
- Docker Desktop ที่เปิด engine แล้ว สำหรับ PostgreSQL 16
- Windows PowerShell: ใช้ npm.cmd/npx.cmd หาก execution policy บล็อก npm.ps1

## ติดตั้งฐานข้อมูลและ Backend

จาก root repository คัดลอกตัวอย่าง config หากยังไม่มี:

```powershell
if (!(Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
```

ตั้ง POSTGRES_PASSWORD และรหัสผ่านใน DATABASE_URL ของ backend/.env ให้ตรงกัน
ใช้รหัสผ่านสำหรับ local development เท่านั้น ห้าม commit .env
ตัวอย่าง config ใช้ port 55432 บน localhost; CORS_ORIGINS เป็น JSON array ของ frontend origins

```powershell
# จาก root repository
docker compose --env-file backend/.env up -d --wait db
cd backend
uv sync --locked
uv run alembic upgrade head
uv run python -m app.seed
uv run fastapi dev
```

- API: http://localhost:8000
- OpenAPI และ interactive examples: http://localhost:8000/docs
- GET /health ตรวจ process; GET /ready ตรวจ database (ไม่พร้อมคืน 503)
- Compose เปิดเฉพาะฐานข้อมูลบน 127.0.0.1:55432 และเก็บข้อมูลใน named volume
- หยุด database จาก root ด้วย `docker compose --env-file backend/.env stop db` โดยยังคงข้อมูลไว้
- ไม่สร้าง schema อัตโนมัติที่ API startup; ใช้ Alembic เท่านั้น

## Backend API

ส่ง `X-User: alice` (หรือ bob, carol, dan) ทุก endpoint ในตาราง
ยังไม่มี full authentication ตามขอบเขตโจทย์

| Method | Endpoint | ผลลัพธ์ |
| --- | --- | --- |
| GET | /groups | array ของ {id, name} เฉพาะกลุ่มของผู้ขอ |
| GET | /groups/{group_id} | {id, name, members} |
| POST | /groups/{group_id}/expenses | Expense; 201 เมื่อสร้าง และ 200 เมื่อ replay |
| GET | /groups/{group_id}/expenses | array ของ Expense ที่ยังไม่ลบ เรียง created_at และ id จากใหม่ไปเก่า |
| DELETE | /groups/{group_id}/expenses/{expense_id} | 204 เฉพาะ payer; soft delete |
| GET | /groups/{group_id}/balances | {group_id, balances: {username: "amount"}} |

POST ต้องส่ง Idempotency-Key ที่ไม่ว่าง ความยาวไม่เกิน 255 ตัวอักษร
ตัวอย่าง request ใน OpenAPI หรือ HTTP client:

```http
POST /groups/1/expenses
Content-Type: application/json
X-User: alice
Idempotency-Key: dinner-0001

{
  "description": "Dinner at the night market",
  "paid_by": "alice",
  "amount": "1000.00",
  "split": {"type": "equal", "members": ["alice", "bob", "carol"]}
}
```

Expense response มี id, group_id, description, paid_by, amount, created_at, is_deleted
และ split รูปแบบเดียวกันทั้ง equal/exact:

```json
{"type": "equal", "shares": {"alice": "333.34", "bob": "333.33", "carol": "333.33"}}
```

สำหรับ exact ให้เปลี่ยน request.split เป็น:

```json
{"type": "exact", "shares": {"alice": "500.00", "bob": "300.00", "carol": "200.00"}}
```

ผล balances สำหรับตัวอย่าง equal คือ alice +666.66, bob -333.33, carol -333.33
API คืนเงินเป็น decimal string ไม่มี comma และมีทศนิยม 2 ตำแหน่งเสมอ
Frontend แสดงรูปแบบตัวเลขไทยและ live preview ตามกติกาเดียวกันกับ Backend

## Business rules และเหตุผลการออกแบบ

- เงิน: Python Decimal และ PostgreSQL NUMERIC(12,2); ไม่ใช้ float คำนวณเงิน
- Input เงินต้องเป็น string ของเลขฐานสิบธรรมดา เช่น "1000", "1000.0", "1000.00"
  ไม่รับ numeric JSON, ค่าติดลบ, exponent, NaN, Infinity หรือทศนิยมเกิน 2 ตำแหน่ง
- Expense ต้องมากกว่า 0 และไม่เกิน 9999999999.99; exact share เป็น 0.00 ได้
- Equal split ใช้จำนวนเต็มสตางค์และ divmod แจกเศษทีละสตางค์ตามลำดับสมาชิกใน request
- Exact shares ต้องรวมตรง amount; ไม่ปัดเศษ input เพื่อทำให้ยอดผ่าน
- ผู้จ่ายและทุกคนใน split ต้องเป็นสมาชิกกลุ่ม; split ต้องไม่ว่างและสมาชิกห้ามซ้ำ
- ผู้ขออาจบันทึกแทน payer คนอื่นในกลุ่มได้ เพราะโจทย์แยก X-User กับ paid_by
  payer ไม่จำเป็นต้องอยู่ในรายชื่อคนแบ่ง แต่ต้องอยู่ในกลุ่ม
- Balance = เงินที่จ่าย - ส่วนที่รับผิดชอบ; ค่าบวกคือต้องได้รับเงิน รวมทุกคนต้องเป็น 0.00
  คืนสมาชิกที่ไม่มียอดด้วยค่า 0.00 และรวมทั้งสองด้านใน SQL statement เดียวเพื่อใช้ snapshot เดียวกัน
- เลือก 403 สำหรับผู้ใช้ที่รู้จักแต่ไม่อยู่ในกลุ่ม เพื่อให้แสดงข้อผิดพลาดตรงสาเหตุ
  กลุ่ม/รายจ่ายที่ไม่มีอยู่คืน 404; รายจ่ายต้องอยู่ใน group ที่ระบุใน path
- X-User หายหรือไม่รู้จักคืน 401; input ผิดคืน 422
- รายจ่ายแก้ไขไม่ได้ (ไม่มี PUT/PATCH); payer เท่านั้นลบได้
  ลบซ้ำโดย payer คืน 204; เก็บ expense/shares ไว้ แต่ไม่รวมรายการที่ลบใน list/balances

### Idempotency และ concurrency

Unique (group_id, idempotency_key) บังคับที่ฐานข้อมูล รวมรายการ soft delete
API ตรวจสิทธิ์สมาชิกก่อนค้นหารายการเดิม จึงใช้ key เพื่อข้ามสิทธิ์ไม่ได้
สำหรับรายการใหม่ ใช้ INSERT ... ON CONFLICT DO NOTHING RETURNING และบันทึก shares ใน transaction เดียวกัน
ถ้าอีก transaction ใช้ key ก่อน จะรอจน transaction นั้นจบ แล้ว SELECT รายการที่ commit แล้ว
ทำงานภายใต้ PostgreSQL READ COMMITTED; ไม่มีการจับ exception แบบกว้างเพื่อเดาว่า key ชน

Key เดิมในกลุ่มเดิมคืน expense แรกแม้ payload เปลี่ยน โดย request ยังต้องผ่าน schema validation
ไม่ตรวจ business fields ใหม่เมื่อพบ key เดิม; กลุ่มต่างกันใช้ key เดียวกันได้
หลัง soft delete การ replay คืน ID เดิมพร้อม is_deleted=true และไม่สร้าง expense ใหม่

### รูปแบบ errors

```json
{"error": {"code": "invalid_split", "message": "The shares do not add up to the total", "details": []}}
```

Validation errors ใช้ code=validation_error พร้อม details ของ location/message/type
ไม่คืน input ที่ผิด, exception context หรือรายละเอียด connection ของฐานข้อมูล
SQL/database errors คืน 503 แบบไม่เปิดเผยข้อมูลภายใน

## Schema และ seed

| Table | หน้าที่และข้อบังคับสำคัญ |
| --- | --- |
| users | username เป็น primary key |
| groups | integer identity ID และชื่อกลุ่ม |
| memberships | primary key (group_id, username) |
| expenses | NUMERIC(12,2), payer membership FK, created_at แบบ timezone, is_deleted |
| expense_shares | NUMERIC(12,2), member membership FK, expense/group FK และ position |

Foreign keys ป้องกันสมาชิกนอกกลุ่มและ shares ที่อ้าง expense คนละกลุ่ม
position เก็บลำดับแจกเศษและ unique ต่อ expense
Indexes รองรับกลุ่มของผู้ใช้, รายจ่ายตาม group/created_at/id และ shares ตามสมาชิก
NUMERIC(12,2) อาจปัดเศษ input เอง จึงต้อง validate ที่ business layer ก่อนบันทึก
ตรวจ schema drift จาก backend/ ด้วย `uv run alembic check`

Seed: alice, bob, carol, dan; group 1 Chiang Mai trip (alice, bob, carol); group 2 Office lunch (bob, dan)
`uv run python -m app.seed` ใช้ transaction, ON CONFLICT DO NOTHING และ advisory lock
เพิ่มเฉพาะข้อมูลที่ขาด ไม่ลบรายจ่ายหรือทับชื่อกลุ่มเดิม; ID ชนกลุ่มชื่ออื่นจะ fail และ rollback
ปรับ group identity sequence ไม่ให้สร้างกลุ่มใหม่ชน ID ที่ seed ไว้
Downgrade ใช้เพื่อพัฒนา/ทดสอบเท่านั้น เพราะลบตารางและข้อมูลของ migration นั้น

## Tests และ code checks

หลังเปิด PostgreSQL และตั้ง backend/.env แล้ว จาก backend/ รัน suite ทั้งหมดด้วยคำสั่งเดียว:

```powershell
uv run pytest
```

รวม required API tests ทั้ง 6 กรณีและ integration tests โดยไม่ต้องตั้ง RUN_DB_TESTS
ใช้ connection จาก DATABASE_URL เพื่อสร้าง database ชั่วคราวชื่อ splitbill_test_<random>
บัญชีทดสอบต้องมีสิทธิ์ CREATE DATABASE และลบ database ที่ตนสร้าง (local Compose มีสิทธิ์นี้)
เทสต์ migrate/seed/constraints และ HTTP API บน database ชั่วคราว แล้วลบทิ้งหลังจบ
ไม่ downgrade หรือล้างข้อมูลของ database พัฒนา
การตรวจ concurrent API บังคับ 4 requests ให้ไปถึงจุด insert พร้อมกันและตรวจว่าได้ expense เดียวกัน

```powershell
# รันเฉพาะ unit tests โดยไม่ใช้ PostgreSQL
uv run pytest -m "not database"
# ตรวจโค้ด
uv run ruff check .
uv run ruff format --check .
```

## Frontend

```powershell
# จาก root repository
cd frontend
npm.cmd ci
if (!(Test-Path .env.local)) { Copy-Item .env.example .env.local }
npm.cmd run dev
```

เปิด http://localhost:3000
NEXT_PUBLIC_API_BASE_URL เป็น URL สาธารณะของ API ห้ามใส่ secrets ในตัวแปร NEXT_PUBLIC_*
หน้าจอเป็นภาษาอังกฤษ: ฟอร์มเพิ่มรายจ่ายด้านซ้าย ยอดสุทธิด้านขวา และรายการรายจ่ายด้านล่าง
บนมือถือเรียงเป็นคอลัมน์เดียว เลือก identity และเฉพาะกลุ่มที่มีสิทธิ์ แล้วเลือก payer และ equal/exact
ดู allocation ก่อนบันทึก กดดูรายละเอียดส่วนแบ่งในแต่ละรายการ และลบได้เฉพาะ payer
การลบมีปุ่มยืนยันในรายการ ไม่เปิด modal ที่ขัดจังหวะการทำงาน

```powershell
# จาก frontend/
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
```

### Money preview และ safe retry

- src/lib/money.ts แปลง string เป็น BigInt หน่วยสตางค์ก่อนคำนวณทั้งหมด ไม่ใช้ Number คำนวณเงิน
- Equal ใช้หารจำนวนเต็มและเศษเหมือน Backend ส่งสมาชิกตาม selection order จึงแจกเศษตรงกัน
- Exact รวมยอดแบบจำนวนเต็ม แสดงยอดยังไม่จัดสรร/เกิน และ disable Save จนยอดรวมตรง
- ค่าใน JSON แปลงกลับเป็น decimal strings ก่อนส่งเสมอ; display จัดกลุ่มหลักพันเองโดยไม่แปลงเป็น float
- ตัวอย่าง 100.00 หาร 3 = 33.34/33.33/33.33 และ 0.10 + 0.20 = 0.30
- สร้าง idempotency key ต่อรายการใหม่ หากเครือข่าย/5xx ทำให้ไม่รู้ผล จะล็อกข้อมูลและ user/group
  เพื่อ retry ด้วย payload และ key เดิม; 4xx แสดง error พร้อมคงฟอร์มให้แก้ไขได้
- กลุ่มที่เปลี่ยนจะสร้าง workspace ใหม่และ abort reads เก่า จึงไม่แสดงข้อมูลจาก scope ก่อนหน้า
- หลังเพิ่ม/ลบ จะโหลด balances/list ใหม่ และซ่อนยอดเดิมระหว่างอัปเดต

### Browser end-to-end tests

เปิด PostgreSQL ตามด้านบน ติดตั้ง frontend dependencies และ Chromium ครั้งแรก:

```powershell
# จาก frontend/
npm.cmd ci
npx.cmd playwright install chromium
# จาก backend/
uv run python -m scripts.test_frontend
```

Runner สร้าง PostgreSQL database ชั่วคราว อัปเดต migrations/seed แล้วเปิด test API บน 8001
และ Next.js บน 3001 ก่อนรัน Playwright ทั้ง desktop (1440px) และ mobile (390px)
ทั้งสอง port ต้องว่าง; database และ test servers ถูก cleanup หลังจบ ไม่แก้ข้อมูลพัฒนา
ไม่ต้องรัน npm run dev หรือ API test server เอง และไม่ควรชี้ browser tests ไปยัง database งานจริง

ครอบคลุม equal/exact preview, การบันทึกและยอดจริง, payer-only deletion, ข้อผิดพลาดจาก API,
การเปลี่ยนผู้ใช้โดยไม่แสดงข้อมูลค้าง และคำตอบหายหลังบันทึกซึ่ง retry ต้องมีเพียงหนึ่ง expense
ภาพหลักอยู่ frontend/test-results/screenshots/desktop.png และ mobile.png; artifacts ไม่เข้า Git

ผลตรวจล่าสุด: unit tests 4 passed, browser tests 8 passed, ESLint/TypeScript/build และ Ruff ผ่าน
รีวิวภาพหน้าจอแยกจากผู้เขียนได้ disposition: ship; detector พบเพียงข้อเสนอเรื่อง system font
ซึ่งเลือกใช้โดยตั้งใจสำหรับหน้าจอ Operate ตามขอบเขต take-home

## โครงสร้าง

- backend/app/api: routing, headers, user/group dependencies และ HTTP response status
- backend/app/services: allocation, zero-sum balances และ expense operations
- backend/app/repositories: SQL และ persistence; core: configuration, sessions และ errors
- backend/app/schemas.py: request/response schemas แยกจาก table models
- backend/tests: unit, schema/migration/seed และ API integration tests
- frontend/src/app: Next.js App Router + Tailwind; components: หน้าจอ/ฟอร์ม/workspace; lib: typed API client และ money helpers
- เก็บ uv.lock และ package-lock.json ใน Git เพื่อให้ติดตั้ง dependencies ซ้ำได้
- .env, dependencies, build outputs และ PDF โจทย์ไม่เข้า Git

## ข้อจำกัดและขั้นตอนถัดไป

Frontend หลักครบแล้ว; pending write/key เก็บในหน่วยความจำ ไม่กู้ข้ามการ refresh หรือปิดแท็บระหว่างส่ง
ตรวจ fresh clone และ dev startup ตาม README แล้ว; ยังไม่ทำ optional settle-up/payments/API containerisation
Repository เป็น public และตรวจเอกสารแล้ว; ผู้สมัครยังต้องกรอกเวลาจริง อ่านโค้ด และยืนยันว่าอธิบายได้ทั้งหมด ดู SUBMISSION.md และ INTERVIEW_PREP.md

## เวลาที่ใช้

ยังไม่ได้รับข้อมูลเวลาทำงานจริงจากผู้ทำ ต้องบันทึกและรวมเวลาจริงก่อนส่งงาน
