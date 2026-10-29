# SplitBill — Checklist

ใช้คู่กับ PLAN.md ติ๊ก [x] เมื่อทำเสร็จและตรวจแล้วเท่านั้น
อัปเดต: Frontend ครบและผ่าน unit tests 4 กรณี, browser tests 8 กรณี (desktop/mobile), lint/typecheck/build และรีวิวภาพหน้าจอ ขั้นถัดไปคือ final review และเตรียมส่ง

วันที่ได้รับโจทย์: __________ | กำหนดส่ง (7 วันปฏิทิน): __________

## 1. Project setup

- [x] สร้าง Git และ GitHub repository: splitbill-take-home
- [x] สร้าง backend/ และ frontend/
- [x] ใช้ Python 3.12+, FastAPI, PostgreSQL 16, Next.js, TypeScript, Tailwind CSS
- [x] ตั้ง .gitignore และไม่ commit secrets, .env, dependencies หรือ build artifacts
- [x] มี .env.example พร้อม placeholder และ config ผ่าน environment variables
- [x] ตั้ง Ruff และ ESLint
- [x] แยก routing, business rules และ data access
- [x] มี README.md และ AI_NOTES.md และอัปเดตระหว่างทำ
- [x] ทยอย commit ตามงานที่เสร็จจริง ไม่ใช่ bulk commit เดียว

## 2. Database และ seed

- [x] Schema ครอบคลุม users, groups, memberships, expenses และ shares
- [x] มี Alembic migrations สร้าง schema จากฐานข้อมูลว่างได้
- [x] เงินใช้ NUMERIC(12,2) และมี constraints/foreign keys ที่จำเป็น
- [x] เก็บสถานะ soft delete ของ expense
- [x] Unique constraint สำหรับ Idempotency-Key ภายในกลุ่มเดียวกัน
- [x] Seed alice, bob, carol และ dan
- [x] Group 1: Chiang Mai trip — alice, bob, carol
- [x] Group 2: Office lunch — bob, dan
- [x] รัน seed ซ้ำแล้วไม่เกิดข้อมูลซ้ำ

## 3. Backend API

- [x] ใช้ X-User ระบุผู้ใช้ พร้อมจัดการ header หาย/ผู้ใช้ไม่พบ
- [x] GET /groups แสดงเฉพาะกลุ่มของผู้ขอ
- [x] GET /groups/{group_id} แสดงกลุ่มพร้อมสมาชิก
- [x] POST /groups/{group_id}/expenses รองรับ equal และ exact
- [x] GET /groups/{group_id}/expenses เรียงใหม่ไปเก่า
- [x] DELETE /groups/{group_id}/expenses/{expense_id} เป็น soft delete
- [x] GET /groups/{group_id}/balances คืนยอดสุทธิสมาชิกทุกคน
- [x] JSON errors รูปแบบสม่ำเสมอและ HTTP status เหมาะสม

## 4. Business rules

- [x] รับ/ส่งเงินเป็น string และ Python ใช้ Decimal ไม่ใช้ float คำนวณเงิน
- [x] Reject expense amount ที่เป็นศูนย์ ติดลบ หรือเกิน 2 ตำแหน่ง
- [x] ตรวจยอดเกินขนาด NUMERIC(12,2) โดยไม่ปล่อยให้เป็น server error
- [x] Equal split แจกเศษทีละสตางค์ตามลำดับสมาชิกใน request
- [x] Exact shares รวมตรง amount ถึงสตางค์ มิฉะนั้น error ชัดเจน
- [x] Payer และผู้ร่วม split ทุกคนเป็นสมาชิกกลุ่ม
- [x] ตรวจ split ว่าง สมาชิกซ้ำ และ share ติดลบ
- [x] เฉพาะสมาชิกอ่านและเขียนกลุ่มได้
- [x] Balance ค่าบวกคือเงินที่สมาชิกต้องได้รับ และรวมทั้งกลุ่มเท่ากับ 0.00
- [x] Key เดิมในกลุ่มเดิมคืน expense แรกโดยไม่สร้างซ้ำ
- [x] Idempotency รับประกันเมื่อส่งคำขอพร้อมกันด้วย transaction/constraint
- [x] ไม่มี endpoint แก้ไข expense
- [x] ลบได้เฉพาะ payer และ record ยังอยู่ในฐานข้อมูล
- [x] Expense ที่ลบไม่รวมใน balances

## 5. Required pytest — รันด้วยคำสั่งเดียว

- [x] 100.00 หาร 3 ได้ 33.34, 33.33, 33.33 และ balances รวม 0.00
- [x] Exact split รวมไม่ตรง amount ถูกปฏิเสธ
- [x] Amount 10.005 ถูกปฏิเสธ
- [x] ส่ง Idempotency-Key ซ้ำแล้วมี expense เดียว
- [x] Alice อ่านและเขียน group 2 ไม่ได้
- [x] เฉพาะ payer ลบ expense ได้

## 6. Additional verification

- [x] Concurrent requests ใช้ key เดียวกัน ได้ expense เดียวและผลรายการเดิม
- [x] Key เดียวกันคนละกลุ่มไม่ชนกัน
- [x] ผู้ไม่มีสิทธิ์ใช้ key เดิมแล้วไม่เห็นข้อมูลรายการ
- [x] Soft delete เก็บ record แต่ยอดคำนวณกลับถูกต้อง
- [x] Payer/สมาชิกนอกกลุ่มถูกปฏิเสธ
- [x] Reject amount <= 0, split ว่าง, สมาชิกซ้ำ และ share ติดลบ
- [x] แจกเศษตามลำดับที่ส่งจริง รวมกรณียอดน้อยกว่าจำนวนสมาชิกเป็นสตางค์
- [x] ตัวอย่าง 1,000.00 ใน PDF ได้ shares 333.34/333.33/333.33 และ balances +666.66/-333.33/-333.33
- [x] Integration tests ตรวจพฤติกรรม PostgreSQL จริง โดยเฉพาะ concurrency

## 7. Frontend

- [x] หน้าเดียว เลือกผู้ใช้และแสดงเฉพาะกลุ่มของผู้ใช้นั้น
- [x] ฟอร์มมี description, amount, payer และ equal/exact split
- [x] Equal เลือกสมาชิกที่ร่วมแบ่งได้
- [x] Exact ระบุยอดแต่ละคนได้
- [x] Preview อัปเดตขณะกรอกและตรงกับ backend ทุกสตางค์
- [x] Exact แสดงยอดยังไม่จัดสรร และ disable submit จนยอดรวมตรง
- [x] คำนวณด้วย integer satang; 0.1 + 0.2 แสดง 0.30
- [x] Format เงินแบบไทย เช่น 1,000.00
- [x] แยกยอดต้องรับและต้องจ่ายอย่างชัดเจน
- [x] แสดง expense list และ balances จาก API
- [x] หลังเพิ่ม/ลบสำเร็จ อัปเดตข้อมูลที่เกี่ยวข้อง
- [x] แสดง API errors เป็นภาษาที่เข้าใจง่าย
- [x] มี loading, empty, error states และป้องกันการส่งซ้ำระหว่างรอ
- [x] Retry รายการเดิมใช้ idempotency key เดิม
- [x] เปลี่ยน user/group แล้วไม่แสดงข้อมูลค้างจากกลุ่มเก่า

## 8. README.md

- [x] วิธี setup จาก fresh clone รวม prerequisites, env, migrate, seed และ start ทั้งสองฝั่ง
- [x] คำสั่งเดียวสำหรับ pytest และคำสั่ง lint/build ที่รันได้จริง
- [x] อธิบาย architecture และการแยกหน้าที่
- [x] อธิบายการเลือก 403/404 พร้อมเหตุผล
- [x] อธิบาย money storage, Decimal, integer satang และรูปแบบ API
- [x] อธิบายการแจกเศษสตางค์และ preview ให้ตรง backend
- [x] อธิบาย idempotency รวม concurrent requests
- [x] บันทึกความกำกวมและสมมติฐานที่เลือกใช้ทั้งหมด
- [ ] ระบุ known limitations, next steps และเวลาที่ใช้โดยประมาณ

## 9. AI_NOTES.md

- [x] ระบุ AI tools ที่ใช้และช่วยงานส่วนใด
- [x] ยกตัวอย่าง prompt ที่ได้ผล 1–2 ตัวอย่าง
- [x] บันทึก AI output ที่ผิด/ไม่ปลอดภัยอย่างน้อย 1 กรณีที่เกิดขึ้นจริง
- [x] อธิบายวิธีตรวจพบและการแก้ไข โดยไม่แต่งเหตุการณ์ขึ้น
- [x] อธิบายกระบวนการ review โค้ดจาก AI ก่อนแต่ละ commit
- [ ] สามารถอธิบายและรับผิดชอบโค้ดที่ส่งได้ทุกส่วน

## 10. Final checks และส่งงาน

- [ ] pytest ผ่านครบ
- [x] Ruff และ ESLint ผ่าน
- [x] TypeScript check และ frontend production build ผ่าน
- [x] ทดสอบใช้งานจริงตั้งแต่เลือก user/group จนเพิ่ม expense และดู balance
- [x] ทดสอบ API การลบและสิทธิ์ผู้ลบจริง
- [ ] ทดลอง setup/test ตาม README จาก fresh clone สำเร็จ
- [ ] ตรวจว่าไม่มี secrets ทั้งไฟล์ปัจจุบันและ Git history
- [ ] ตรวจ incremental commit history และเอกสารฉบับสุดท้าย
- [ ] Repository เป็น public หรือแชร์ private กับ @alkchowpa แล้ว
- [ ] ส่งลิงก์ repository ภายในกำหนด
- [ ] เตรียม walkthrough 15 นาที, live change 20 นาที, คำถาม 10 นาที

## 11. Optional — เริ่มหลังงานบังคับเสร็จและผ่าน tests

- [ ] Docker Compose เปิด API และ PostgreSQL ด้วยคำสั่งเดียว
- [ ] GET /groups/{group_id}/settle-up ให้จำนวนรายการจ่ายน้อยที่สุด พร้อม tests
- [ ] POST /groups/{group_id}/payments บันทึกคืนเงินและอัปเดต balances พร้อม tests
