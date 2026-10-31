# Final review and fresh-clone verification

สรุปผลวันที่ 31 ตุลาคม 2026 (Asia/Bangkok)
ตรวจ runtime ของ commit `b9fea9a4716d9b720ad1931627622c95fb8022a2` เมื่อ 29 ตุลาคม และยืนยันผล browser suite ที่บันทึกไว้เมื่อกลับมาทำงานต่อ
GitHub main ตรงกับ code commit นี้ตอนเริ่มตรวจวันที่ 31 ตุลาคม; commits หลังจากนั้นเป็นเอกสาร review/handoff โดยไม่เปลี่ยน application code

## ผลรีวิว

ไม่พบปัญหาที่ขัดขวาง required scope จากการอ่านโค้ดและผลตรวจด้านล่าง
ตรวจ access control, exact/equal allocation, zero-sum balances, monetary precision,
idempotency/transaction boundaries, soft delete, frontend request scoping และ safe retry
ตรวจ README, AI_NOTES และ incremental commit history ซึ่งแยก setup/database/API/frontend เป็นงานย่อย

## Fresh clone

- ใช้ `git clone --no-local` จาก Git repository ในเครื่องไป directory ใหม่ ไม่มี node_modules, .venv หรือ .env เดิม
- ติดตั้งด้วย `uv sync --locked` และ `npm.cmd ci` โดยใช้ lockfiles ที่ commit แล้ว
- สร้าง environment config ใหม่จากตัวอย่าง ใช้รหัสผ่านทดสอบที่ไม่เข้า Git
- เปิด PostgreSQL 16 ด้วย Compose project/volume แยก โดย override host port เป็น 55433 แทน 55432 เพื่อไม่ชนข้อมูลพัฒนา
- ไม่มีการแก้ source ใน clone; `git status --short` ว่างหลังติดตั้งและตรวจ
- Package caches และ Chromium ที่ติดตั้งในเครื่องถูกใช้ซ้ำตามปกติ ไม่ได้ทดสอบบน OS หรือเครื่องใหม่

| ตรวจ | ผล |
| --- | --- |
| Alembic upgrade จาก database ว่าง | ผ่าน |
| Seed สองรอบ | ผ่าน; 4 users, 2 groups, 5 memberships โดยไม่ซ้ำ |
| Backend pytest รวม PostgreSQL จริง | 70 passed |
| Ruff check และ format check | ผ่าน |
| Alembic schema drift check | ไม่พบ upgrade operations ใหม่ |
| Frontend money unit tests | 4 passed |
| ESLint และ TypeScript | ผ่าน |
| Next.js production build | ผ่าน |
| Browser tests: Chromium desktop/mobile | 8 passed; .last-run.json มี status=passed และ failedTests=[] |
| Git tracked source ใน clone | ไม่มีการเปลี่ยนแปลง |

เปิดด้วยคำสั่ง dev ตาม README จริง: `uv run fastapi dev` และ `npm.cmd run dev`
GET /ready คืน ok, GET /groups ของ alice คืน Chiang Mai trip, หน้าเว็บ HTTP 200 และแสดง heading
CORS อนุญาต http://localhost:3000 และ headers ของการเพิ่มรายจ่าย
Browser suite ตรวจ UI → API → PostgreSQL → balances/list รวมการลบ, exact validation,
API errors, user switch และ response หายหลังบันทึกซึ่ง retry ต้องไม่สร้างรายการซ้ำ

Test servers หยุดแล้ว และลบ Compose container/network/volume ของ project ทดสอบแล้ว
ฐานข้อมูลพัฒนาเดิมไม่ได้ถูกล้างหรือ migrate โดยการตรวจชุดนี้

## Repository และ secrets

- Repository `napat-atng/splitbill-take-home` เป็น public; main ตรงกับ code commit ที่ตรวจ
- สแกน Git history 96 unique blobs รวม tracked files ทุก revision ที่มีอยู่ ณ การตรวจ
- ไม่พบ patterns ของ GitHub/OpenAI tokens, AWS access key, private keys หรือ credential URLs ที่เป็นค่าจริง
- ไม่พบ .env หรือ PDF ใน history; .env.example ใช้ placeholders
- การตรวจเป็น pattern scan ร่วมกับ file/history review ไม่ได้ใช้ hosted secret-scanning service
- เอกสาร final review commit หลัง code commit ที่ตรวจ ไม่มีการแก้ application code

## สิ่งที่ยังต้องทำก่อนส่ง

- ผู้สมัครกรอกเวลาทำงานโดยประมาณและวันรับโจทย์/กำหนดส่งจริง ห้ามใช้เวลาระหว่าง commits แทนเวลาทำงานจริง
- ผู้สมัครอ่านโค้ดและยืนยันว่าอธิบายได้ทั้งหมด พร้อมเตรียม walkthrough/live change
- ส่งลิงก์ repository ภายในกำหนดตาม draft ใน SUBMISSION.md; มีคู่มือซ้อมใน INTERVIEW_PREP.md แล้ว

ข้อจำกัดที่ยอมรับ: pending frontend write/key ไม่กู้ข้ามการ refresh/ปิดแท็บ;
browser suite ตรวจ Chromium เท่านั้น; optional settle-up/payments/API containerisation ยังไม่ได้ทำ