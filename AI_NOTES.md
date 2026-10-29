# AI Notes

## เครื่องมือและส่วนที่ช่วย

ใช้ Codex อ่านโจทย์ สรุปข้อกำหนด สร้าง PLAN.md/CHECKLIST.md และ .gitignore
ใช้สกิล find-skills และ manage-skills-hub ค้นหาและติดตั้งสกิล fastapi ทางการ
ใช้สกิล fastapi ช่วยตั้งโครง API, response models และ config
ใช้ create-next-app สร้าง Next.js + TypeScript + Tailwind + ESLint scaffold
Codex ช่วยสร้าง health/CORS tests, คำสั่งตรวจ และเอกสารตั้งต้น

## ตัวอย่าง prompts จากการทำงานจริง

1. “เริ่มจากสร้าง md สำหรับ plan and checklist สิ่งที่ต้องทำทั้งหมด”
2. “ช่วย checklist สิ่งที่ทำไปแล้ว ตอนนี้มี repo ใน github แล้ว เริ่มทำตามขั้นตอนต่อไปได้”

## ข้อผิดพลาดจาก AI และการแก้ไข

Codex ใช้ Set-Content -Encoding utf8 ใน Windows PowerShell เพื่อสร้าง pyproject.toml
คำสั่งนี้เขียน UTF-8 BOM ซึ่งทำให้ pytest แจ้ง Invalid statement ที่บรรทัด 1 คอลัมน์ 1
และ ruff format เกิด panic ระหว่างอ่าน config
ตรวจด้วย Format-Hex พบ prefix EF BB BF จึงเปลี่ยนไฟล์ที่เกี่ยวข้องเป็น UTF-8 ไม่มี BOM
จากนั้นรัน pytest และ Ruff ใหม่เพื่อยืนยันผล (ดูผลการตรวจในประวัติการทำงาน)
อีกกรณี: ใช้ npm ผ่าน PowerShell แล้วถูก execution policy บล็อก จึงใช้ npm.cmd/npx.cmd
โดยไม่เปลี่ยนนโยบายความปลอดภัยของเครื่อง

## กระบวนการ review ก่อน commit

- ตรวจ diff ว่าตรงกับขั้นตอนงานและไม่รวม PDF, .env, dependencies หรือ secrets
- รัน checks ที่เกี่ยวข้อง: pytest, Ruff, ESLint, TypeScript และ build
- ตรวจผลจริงก่อนติ๊ก checklist; ฟีเจอร์ที่เป็นเพียงโครงยังไม่ถือว่าเสร็จ
- ผู้สมัครต้องอ่านและทำความเข้าใจโค้ด รวมถึงยืนยันการ review ของตนก่อนส่งงาน

## งานที่ต้องเติมก่อนส่ง

บันทึกการใช้ AI ในขั้นตอนถัดไป ผลตรวจและการแก้ไขที่เกิดขึ้นจริง
ผู้สมัครต้องยืนยันว่าอธิบายโค้ดทั้งหมดได้ และระบุเวลาทำงานจริงใน README

## ต่อเติม Project setup

เพิ่ม PostgreSQL 16 ผ่าน Docker Compose แบบ local-only, pooled SQLModel engine และ session dependency
แยก readiness route → repository และกติกาเงินใน services/money.py ซึ่งไม่ import HTTP/database
เพิ่ม tests ของการแจกเศษ ลำดับสมาชิก และยอดที่ไม่ถูกต้อง; schema และ expense API ยังไม่เสร็จ

ผลตรวจ: pytest 12 passed, Ruff check/format ผ่าน, PostgreSQL 16.15 และ TestClient GET /ready คืน 200 โดยใช้ connection จริง
