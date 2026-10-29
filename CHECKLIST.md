# SplitBill — Checklist

ใช้คู่กับ PLAN.md ติ๊ก [x] เมื่อทำเสร็จและตรวจแล้วเท่านั้น
อัปเดต: Project setup และ Database/seed ครบแล้ว; PostgreSQL integration tests รวม unit tests 29 กรณีผ่าน, Ruff และ Alembic schema drift check ผ่าน ขั้นถัดไปคือกติกาเงินส่วนที่เหลือและ Backend API

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

- [ ] ใช้ X-User ระบุผู้ใช้ พร้อมจัดการ header หาย/ผู้ใช้ไม่พบ
- [ ] GET /groups แสดงเฉพาะกลุ่มของผู้ขอ
- [ ] GET /groups/{group_id} แสดงกลุ่มพร้อมสมาชิก
- [ ] POST /groups/{group_id}/expenses รองรับ equal และ exact
- [ ] GET /groups/{group_id}/expenses เรียงใหม่ไปเก่า
- [ ] DELETE /groups/{group_id}/expenses/{expense_id} เป็น soft delete
- [ ] GET /groups/{group_id}/balances คืนยอดสุทธิสมาชิกทุกคน
- [ ] JSON errors รูปแบบสม่ำเสมอและ HTTP status เหมาะสม

## 4. Business rules

- [ ] รับ/ส่งเงินเป็น string และ Python ใช้ Decimal ไม่ใช้ float คำนวณเงิน
- [ ] Reject expense amount ที่เป็นศูนย์ ติดลบ หรือเกิน 2 ตำแหน่ง
- [ ] ตรวจยอดเกินขนาด NUMERIC(12,2) โดยไม่ปล่อยให้เป็น server error
- [x] Equal split แจกเศษทีละสตางค์ตามลำดับสมาชิกใน request
- [ ] Exact shares รวมตรง amount ถึงสตางค์ มิฉะนั้น error ชัดเจน
- [ ] Payer และผู้ร่วม split ทุกคนเป็นสมาชิกกลุ่ม
- [ ] ตรวจ split ว่าง สมาชิกซ้ำ และ share ติดลบ
- [ ] เฉพาะสมาชิกอ่านและเขียนกลุ่มได้
- [ ] Balance ค่าบวกคือเงินที่สมาชิกต้องได้รับ และรวมทั้งกลุ่มเท่ากับ 0.00
- [ ] Key เดิมในกลุ่มเดิมคืน expense แรกโดยไม่สร้างซ้ำ
- [ ] Idempotency รับประกันเมื่อส่งคำขอพร้อมกันด้วย transaction/constraint
- [ ] ไม่มี endpoint แก้ไข expense
- [ ] ลบได้เฉพาะ payer และ record ยังอยู่ในฐานข้อมูล
- [ ] Expense ที่ลบไม่รวมใน balances

## 5. Required pytest — รันด้วยคำสั่งเดียว

- [ ] 100.00 หาร 3 ได้ 33.34, 33.33, 33.33 และ balances รวม 0.00
- [ ] Exact split รวมไม่ตรง amount ถูกปฏิเสธ
- [ ] Amount 10.005 ถูกปฏิเสธ
- [ ] ส่ง Idempotency-Key ซ้ำแล้วมี expense เดียว
- [ ] Alice อ่านและเขียน group 2 ไม่ได้
- [ ] เฉพาะ payer ลบ expense ได้

## 6. Additional verification

- [ ] Concurrent requests ใช้ key เดียวกัน ได้ expense เดียวและผลรายการเดิม
- [ ] Key เดียวกันคนละกลุ่มไม่ชนกัน
- [ ] ผู้ไม่มีสิทธิ์ใช้ key เดิมแล้วไม่เห็นข้อมูลรายการ
- [ ] Soft delete เก็บ record แต่ยอดคำนวณกลับถูกต้อง
- [ ] Payer/สมาชิกนอกกลุ่มถูกปฏิเสธ
- [ ] Reject amount <= 0, split ว่าง, สมาชิกซ้ำ และ share ติดลบ
- [ ] แจกเศษตามลำดับที่ส่งจริง รวมกรณียอดน้อยกว่าจำนวนสมาชิกเป็นสตางค์
- [ ] ตัวอย่าง 1,000.00 ใน PDF ได้ shares 333.34/333.33/333.33 และ balances +666.66/-333.33/-333.33
- [ ] Integration tests ตรวจพฤติกรรม PostgreSQL จริง โดยเฉพาะ concurrency

## 7. Frontend

- [ ] หน้าเดียว เลือกผู้ใช้และแสดงเฉพาะกลุ่มของผู้ใช้นั้น
- [ ] ฟอร์มมี description, amount, payer และ equal/exact split
- [ ] Equal เลือกสมาชิกที่ร่วมแบ่งได้
- [ ] Exact ระบุยอดแต่ละคนได้
- [ ] Preview อัปเดตขณะกรอกและตรงกับ backend ทุกสตางค์
- [ ] Exact แสดงยอดยังไม่จัดสรร และ disable submit จนยอดรวมตรง
- [ ] คำนวณด้วย integer satang; 0.1 + 0.2 แสดง 0.30
- [ ] Format เงินแบบไทย เช่น 1,000.00
- [ ] แยกยอดต้องรับและต้องจ่ายอย่างชัดเจน
- [ ] แสดง expense list และ balances จาก API
- [ ] หลังเพิ่ม/ลบสำเร็จ อัปเดตข้อมูลที่เกี่ยวข้อง
- [ ] แสดง API errors เป็นภาษาที่เข้าใจง่าย
- [ ] มี loading, empty, error states และป้องกันการส่งซ้ำระหว่างรอ
- [ ] Retry รายการเดิมใช้ idempotency key เดิม
- [ ] เปลี่ยน user/group แล้วไม่แสดงข้อมูลค้างจากกลุ่มเก่า

## 8. README.md

- [ ] วิธี setup จาก fresh clone รวม prerequisites, env, migrate, seed และ start ทั้งสองฝั่ง
- [ ] คำสั่งเดียวสำหรับ pytest และคำสั่ง lint/build ที่รันได้จริง
- [ ] อธิบาย architecture และการแยกหน้าที่
- [ ] อธิบายการเลือก 403/404 พร้อมเหตุผล
- [ ] อธิบาย money storage, Decimal, integer satang และรูปแบบ API
- [ ] อธิบายการแจกเศษสตางค์และ preview ให้ตรง backend
- [ ] อธิบาย idempotency รวม concurrent requests
- [ ] บันทึกความกำกวมและสมมติฐานที่เลือกใช้ทั้งหมด
- [ ] ระบุ known limitations, next steps และเวลาที่ใช้โดยประมาณ

## 9. AI_NOTES.md

- [x] ระบุ AI tools ที่ใช้และช่วยงานส่วนใด
- [x] ยกตัวอย่าง prompt ที่ได้ผล 1–2 ตัวอย่าง
- [x] บันทึก AI output ที่ผิด/ไม่ปลอดภัยอย่างน้อย 1 กรณีที่เกิดขึ้นจริง
- [x] อธิบายวิธีตรวจพบและการแก้ไข โดยไม่แต่งเหตุการณ์ขึ้น
- [ ] อธิบายกระบวนการ review โค้ดจาก AI ก่อนแต่ละ commit
- [ ] สามารถอธิบายและรับผิดชอบโค้ดที่ส่งได้ทุกส่วน

## 10. Final checks และส่งงาน

- [ ] pytest ผ่านครบ
- [ ] Ruff และ ESLint ผ่าน
- [ ] TypeScript check และ frontend production build ผ่าน
- [ ] ทดสอบใช้งานจริงตั้งแต่เลือก user/group จนเพิ่ม expense และดู balance
- [ ] ทดสอบ API การลบและสิทธิ์ผู้ลบจริง
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
