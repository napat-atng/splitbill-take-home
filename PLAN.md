# SplitBill — Implementation Plan

แผนจาก Developer-Take-Home-Test.pdf ใช้คู่กับ CHECKLIST.md
สถานะ: วางแผนแล้ว ยังไม่ได้เริ่ม implementation
ชื่อ repository ที่แนะนำ: splitbill-take-home
กำหนดส่ง: ภายใน 7 วันปฏิทินนับจากได้รับโจทย์ (ต้องกรอกวันที่รับและวันส่งจริง)

## เป้าหมายและขอบเขต

สร้างแอปหารค่าใช้จ่ายในกลุ่ม คำนวณแม่นยำถึงสตางค์ พร้อม API และหน้าเว็บที่ใช้งานร่วมกันได้
เน้น business rules และ tests ก่อนความสวยงามและฟีเจอร์เสริม
ใช้ Python 3.12+, FastAPI, PostgreSQL 16, Alembic และ Next.js + TypeScript + Tailwind CSS
ไม่ทำระบบล็อกอินเต็มรูปแบบ ใช้ X-User ตามโจทย์ และไม่ทำฟีเจอร์แก้ไขรายจ่าย

## ลำดับดำเนินงาน

ทำตามขั้นตอนด้านล่างโดยไม่ผูกกับจำนวนวัน สามารถทำหลายขั้นตอนหรือทั้งหมดในวันเดียวได้ เมื่อทำงานและตรวจสอบของขั้นตอนนั้นครบแล้วจึงไปขั้นตอนถัดไป โดยใช้ CHECKLIST.md ติดตามความคืบหน้า

### ขั้นตอนที่ 1: ตั้งโปรเจกต์และบันทึกการทำงาน

- สร้าง Git repository และ GitHub repository แยก backend/ กับ frontend/
- เพิ่ม .gitignore, .env.example, README.md และ AI_NOTES.md ตั้งแต่ต้น
- ตั้ง dependencies, Ruff, ESLint และคำสั่งทดสอบที่รันซ้ำได้
- จดสมมติฐาน การตัดสินใจ เวลาที่ใช้ และการใช้ AI ระหว่างทำ
- ทยอย commit ตามงานที่เสร็จ ห้ามรวมทุกอย่างเป็น commit เดียว

### ขั้นตอนที่ 2: ฐานข้อมูลและกติกาเงิน

- แยก routing, business logic และ data access ออกจากกัน
- ออกแบบ users, groups, memberships, expenses และ expense shares พร้อม foreign keys
- เก็บเงินด้วย NUMERIC(12,2); ใช้ Decimal ใน Python และส่ง/รับเงินเป็น string
- เก็บสถานะ soft delete และ Idempotency-Key โดยมี unique constraint ระดับกลุ่ม
- ทำ Alembic migrations และ seed ที่รันซ้ำได้
- Seed users: alice, bob, carol, dan
- Seed group 1: Chiang Mai trip — alice, bob, carol; group 2: Office lunch — bob, dan
- ทำ equal split โดยแจกเศษสตางค์ตามลำดับสมาชิกใน request และ exact split ที่รวมตรงยอด
- คำนวณ balance = เงินที่จ่ายออก - ส่วนที่ต้องรับผิดชอบ; ค่าบวกหมายถึงต้องได้รับเงิน
- เขียน unit tests ของกติกาเงินก่อนเชื่อม API

### ขั้นตอนที่ 3: Backend และ integration tests

| Method | Endpoint | หน้าที่ |
| --- | --- | --- |
| GET | /groups | กลุ่มของผู้ใช้ที่ส่ง X-User |
| GET | /groups/{group_id} | รายละเอียดกลุ่มและสมาชิก |
| POST | /groups/{group_id}/expenses | เพิ่มรายจ่ายแบบ equal/exact |
| GET | /groups/{group_id}/expenses | รายจ่ายเรียงใหม่ไปเก่า |
| DELETE | /groups/{group_id}/expenses/{expense_id} | soft delete โดยผู้จ่ายเท่านั้น |
| GET | /groups/{group_id}/balances | ยอดสุทธิสมาชิกทุกคน |

- ตรวจ X-User และ membership ทุก endpoint ของกลุ่ม รวมก่อนคืนผลจาก idempotency
- ตรวจ payer และผู้ร่วม split ว่าอยู่ในกลุ่ม; ยอดรายจ่ายต้องมากกว่า 0 และไม่เกิน 2 ตำแหน่ง
- Exact shares ต้องรวมตรง amount ถึงสตางค์; ไม่ใช้ float ในเส้นทางคำนวณเงิน
- ใช้ transaction และ database uniqueness รับประกันว่าคำขอพร้อมกันไม่สร้างรายจ่ายซ้ำ
- Key ซ้ำในกลุ่มเดิมต้องคืนรายจ่ายที่สร้างครั้งแรก; group ต่างกันใช้ key เดียวกันได้
- รายจ่ายแก้ไขไม่ได้; soft-deleted expenses ไม่รวมใน balances
- ส่ง JSON errors รูปแบบเดียวกันพร้อม HTTP status ที่เหมาะสม
- รัน integration tests กับ PostgreSQL เพื่อทดสอบ constraints และ concurrency จริง

### ขั้นตอนที่ 4: Frontend

- ทำหน้าเดียว เลือกผู้ใช้ แล้วโหลดเฉพาะกลุ่มของผู้ใช้นั้น
- ฟอร์มมี description, amount, payer, split type และสมาชิก/ยอดแต่ละคน
- ใช้จำนวนเต็มหน่วยสตางค์สำหรับ preview และแปลงเป็น string เมื่อส่ง API
- Equal preview ใช้ลำดับแจกเศษเหมือน backend; exact แสดงยอดยังไม่จัดสรรและปิด submit จนรวมตรง
- แสดงจำนวนเงินรูปแบบไทย เช่น 1,000.00 และแยกยอดต้องรับ/ต้องจ่ายให้ชัดเจน
- โหลด balances และ expense list ใหม่หลังเพิ่มหรือลบสำเร็จ
- สร้าง idempotency key ต่อการส่งใหม่ และใช้ key เดิมเมื่อลองส่งรายการเดิมซ้ำหลังเครือข่ายผิดพลาด
- รองรับ loading, empty และ error states; เปลี่ยน user/group แล้วไม่แสดงข้อมูลค้างจากกลุ่มก่อน
- แปลง API errors เป็นภาษาที่เข้าใจง่ายและคงข้อมูลในฟอร์มเมื่อส่งไม่สำเร็จ

### ขั้นตอนที่ 5: ตรวจระบบและเอกสาร

- ทดสอบ flow เลือกผู้ใช้ → เลือกกลุ่ม → เพิ่ม expense → ตรวจยอด → ลบโดย payer
- ตรวจกรณีแบ่ง 100.00 ได้ 33.34/33.33/33.33 และ 0.1 + 0.2 แสดง 0.30
- รัน pytest, Ruff, ESLint, TypeScript check และ frontend production build
- ทดลอง fresh clone, ตั้งค่า env, migrate, seed, start และ test ตาม README
- ตรวจ repository ว่าไม่มี secrets และ commit history แสดงพัฒนาการจริง

### ขั้นตอนที่ 6: เตรียมส่งและสัมภาษณ์

- เติม README และ AI_NOTES ให้ครบ ตรวจลิงก์และสิทธิ์ repository
- ส่งลิงก์ public repository หรือ private ที่แชร์กับ @alkchowpa
- เตรียม walkthrough 15 นาที อธิบาย design decisions และโค้ดที่ AI ช่วยเขียน
- เตรียม live change 20 นาที และคำถามเกี่ยวกับบริษัท/บทบาท 10 นาที

## ค่าเริ่มต้นที่เสนอสำหรับ implementation

ข้อเหล่านี้เป็นการตัดสินใจของโปรเจกต์ ต้องบันทึกใน README ไม่ใช่ข้อกำหนดเพิ่มเติมจากโจทย์

- ใช้ 403 สำหรับผู้ใช้ที่มีอยู่แต่ไม่ได้เป็นสมาชิกกลุ่ม; กลุ่มที่ไม่มีอยู่ใช้ 404
- ไม่บังคับให้ X-User เท่ากับ paid_by เพราะโจทย์ให้เลือก payer; ทั้งสองต้องเป็นสมาชิก และผู้ลบต้องเป็น payer
- Expense list ซ่อนรายการที่ soft delete; ยังเก็บข้อมูลในฐานข้อมูลเพื่อ audit
- Key ซ้ำคืนข้อมูลรายการเดิมโดยไม่สร้างใหม่ แม้ payload ต่างกัน; ไม่สร้างใหม่หลังรายการเดิมถูกลบ
- ตรวจ missing/unknown X-User, สมาชิกซ้ำ, split ว่าง, shares ติดลบ และยอดเกิน NUMERIC(12,2) พร้อม error ที่ชัดเจน
- อนุญาต exact share เป็น 0.00 แต่ไม่อนุญาตค่าติดลบ; ยอด expense รวมต้องมากกว่า 0
- Deployment ไม่ใช่งานบังคับ; ทำให้ติดตั้งและรันจาก fresh clone ได้ก่อน

## งานเสริม — ทำหลังงานบังคับผ่านทั้งหมด

1. Docker Compose เปิด API และ PostgreSQL ด้วยคำสั่งเดียว
2. GET /groups/{group_id}/settle-up ให้ชุดการจ่ายที่มีจำนวนรายการน้อยที่สุดตามโจทย์; ต้องพิสูจน์ด้วย tests
3. POST /groups/{group_id}/payments บันทึกการคืนเงินและอัปเดตยอด

## เกณฑ์จบงาน

งานบังคับทุกข้อใน CHECKLIST.md ผ่าน มีหลักฐานการตรวจจริง รันได้จาก fresh clone และผู้ทำอธิบายโค้ดทั้งหมดได้
น้ำหนักคะแนน: business rules 35%, tests 20%, code quality 15%, frontend 15%, เอกสารและ commit history 15%

