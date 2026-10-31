# Interview preparation — SplitBill

คู่มือซ้อมจาก implementation จริง ผู้สมัครต้องอ่านและทดลองเองก่อนสัมภาษณ์
เอกสารนี้ไม่ใช่หลักฐานว่าผู้สมัครเข้าใจหรือได้ซ้อมแล้ว

## Walkthrough — 15 minutes

| เวลา | ประเด็น | สิ่งที่เปิดให้ดู |
| --- | --- | --- |
| 0–2 นาที | งานที่แก้: ค่าใช้จ่ายกลุ่ม แบ่งเท่ากันหรือระบุยอด และยอดสุทธิ | หน้าเว็บ: เลือก alice / Chiang Mai trip |
| 2–5 นาที | Demo รายจ่าย 100.00 หาร 3 เป็น 33.34/33.33/33.33; ลอง exact ที่ยอดไม่ตรง | ฟอร์ม preview, balances, expense details |
| 5–8 นาที | HTTP → service → repository และ membership checks | backend/app/api/groups.py, dependencies.py, services/expenses.py |
| 8–11 นาที | เงินและ concurrent idempotency | services/money.py, repositories/expenses.py, models.py |
| 11–13 นาที | Frontend และ safe retry | frontend/src/lib/money.ts, api.ts, components/expense-form.tsx |
| 13–15 นาที | Tests, tradeoffs, AI review และข้อจำกัด | tests/test_api.py, tests/e2e/splitbill.spec.ts, README.md, AI_NOTES.md |

### Demo ที่ควรซ้อม

1. เปิด API และ Frontend ตาม README; เริ่มจากกลุ่มที่ไม่มีรายจ่ายอื่น หรืออธิบายยอดเดิมให้ชัดเจน
2. กรอก Dinner 100.00 โดย alice; preview ต้องแจกเศษให้ alice ก่อนตามลำดับสมาชิกที่ส่ง
3. บันทึกแล้วเห็น alice +66.66, bob/carol -33.33 หากเป็นรายจ่ายเดียวของกลุ่ม
4. เปลี่ยนเป็น exact: 50.00/49.99/0.00 จะเหลือ 0.01 และ Save ถูกปิด
5. เปลี่ยนเป็น bob เพื่อแสดงว่าไม่มีปุ่มลบรายการของ alice; กลับเป็น alice แล้วลบและตรวจยอด
6. แสดงว่า bob เลือก Office lunch ได้ แต่ alice ไม่เห็นกลุ่มนั้น; API ทดสอบการฝืนเข้าถึงด้วย 403

## จุดที่ต้องอธิบายด้วยคำของตัวเอง

### Money and allocation

- Backend รับ string → Decimal → NUMERIC(12,2); ไม่ใช้ float สำหรับเงิน
- Reject ทศนิยมเกิน 2 ตำแหน่งก่อนบันทึก เพราะฐานข้อมูลอาจปัดเศษ input เอง
- Equal: เปลี่ยนยอดเป็นสตางค์ แล้วใช้ divmod; แจก remainder ทีละ 1 สตางค์ตาม request order
- Exact: อนุญาต share เป็นศูนย์ แต่ห้ามติดลบ และ sum ต้องตรง amount
- Frontend ใช้ BigInt หน่วยสตางค์ ทำกติกาเดียวกัน ก่อนส่งต้องแปลงกลับเป็น string เพราะ JSON ไม่รองรับ BigInt โดยตรง

### Balances

- Net = paid - allocated share; บวกคือต้องได้รับเงิน ลบคือต้องจ่าย
- Repository รวมด้าน paid และ owed ใน SQL statement เดียวเพื่อใช้ snapshot เดียวกัน
- ไม่นำ soft-deleted expenses มาคำนวณ และรวมสมาชิกที่ไม่มียอดด้วย 0.00
- Service ตรวจว่าผลรวมเป็นศูนย์และไม่มีสมาชิกแปลกปลอมใน ledger

### Idempotency and transactions

- Key scope คือ (group_id, idempotency_key) และ unique constraint ไม่ยกเว้นรายการที่ลบ
- ตรวจสิทธิ์ก่อน lookup key จึงใช้ key เพื่อข้ามสิทธิ์ไม่ได้
- SELECT ก่อน insert อย่างเดียวไม่พอสำหรับ concurrency; ต้องอาศัย database uniqueness
- INSERT ... ON CONFLICT DO NOTHING RETURNING รอ transaction คู่แข่ง แล้วอ่านรายการที่ commit แล้วภายใต้ READ COMMITTED
- Expense และ shares ถูก commit ใน transaction เดียว จึงไม่เห็นรายจ่ายครึ่งรายการผ่าน API
- ครั้งแรก 201; replay 200 พร้อม expense เดิม; payload ที่ schema-valid เปลี่ยนได้แต่ไม่สร้างรายการใหม่
- Frontend เก็บ payload/key เดิมเมื่อไม่รู้ผล และล็อกข้อมูลระหว่าง retry
- ข้อจำกัดจริง: pending key อยู่ใน memory ไม่คงข้าม refresh/ปิดแท็บ

### Access, deletion and errors

- X-User เป็น identity สำหรับโจทย์ ไม่ใช่ authentication สำหรับ production
- ผู้ใช้ที่รู้จักแต่ไม่อยู่ในกลุ่มได้ 403 เพื่อแสดงเหตุผลตรง; กลุ่ม/expense ที่ไม่พบได้ 404
- X-User หาย/ไม่รู้จักได้ 401; input ผิดได้ 422
- ผู้ขอบันทึกแทน payer ในกลุ่มได้ตามสมมติฐานที่บันทึกไว้; payer เท่านั้นลบได้
- ไม่มี PUT/PATCH; DELETE เป็น soft delete และลบซ้ำโดย payer ได้ 204
- Errors เป็น JSON envelope เดียวกัน ไม่ส่ง raw input/exception context/connection details กลับผู้ใช้

### Tests and AI use

- Backend 70 tests, frontend money 4 tests และ browser 8 tests ผ่านในการตรวจ fresh clone
- PostgreSQL tests และ browser tests ใช้ database ชั่วคราว ไม่ล้างฐานข้อมูลพัฒนา
- Concurrent API test บังคับ 4 requests ให้มาถึงจุด insert พร้อมกัน ไม่ใช้ sleep เพื่อหวังให้ชน
- Browser lost-response test ให้ server บันทึกจริง แล้วตัด response ก่อน retry และตรวจว่ามี expense เดียว
- อธิบายตัวอย่าง AI ผิดจาก AI_NOTES: UTF-8 BOM ใน TOML หรือ selector alert ที่กว้างจนชน Next.js announcer
- ห้ามอ้างว่าตน review/เข้าใจส่วนที่ยังไม่ได้อ่าน ให้ใช้รายการนี้ชี้จุดที่ต้องเรียนรู้ก่อนสัมภาษณ์

## Live change — 20 minutes

ลำดับซ้อม: ทวน requirement → หาจุดแก้ → เพิ่ม/ปรับ test → implement เล็กที่สุด → รัน checks → อธิบายผลและข้อจำกัด
ตัวอย่างฝึก ไม่ใช่ฟีเจอร์ที่อ้างว่าทำแล้ว:

- จำกัด description จาก 500 เป็น 200: ปรับ request schema และ frontend maxLength พร้อม API validation test
  ไม่ต้องลด column 500 ถ้าข้อกำหนดเปลี่ยนเฉพาะ input limit; ถ้าต้องลด storage limit ให้เพิ่ม migration ใหม่และพิจารณาข้อมูลเก่า
- เพิ่ม payer filter ของ expense list: เริ่มจาก query parameter → repository predicate และ group-access test
- เปลี่ยนข้อความ validation: แก้ที่ต้นทางของ error และตรวจ UI error mapping ไม่ hardcode ข้อความต่างกันสองฝั่ง

คำสั่งสำคัญ:

```powershell
# backend/
uv run pytest
uv run ruff check .
uv run ruff format --check .
# frontend/
npm.cmd test
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
# backend/ — ใช้ PostgreSQL และเริ่ม test servers เอง
uv run python -m scripts.test_frontend
```

## Questions for the team — 10 minutes

เลือกถามตามเวลาจริง 2–3 ข้อ:

- ทีมคาดหวังอะไรจากคนในบทบาทนี้ใน 3 เดือนแรก?
- งาน backend/frontend ในทีมแบ่งความรับผิดชอบและ review กันอย่างไร?
- ทีมใช้ automated tests และ deploy workflow แบบใด?
- ปัญหาที่ทีมอยากให้คนใหม่มาช่วยแก้มากที่สุดคืออะไร?
- ทีมมีแนวทางใช้ AI และตรวจโค้ดที่ AI ช่วยเขียนอย่างไร?

## ผู้สมัครยืนยันเอง

- [ ] อธิบาย flow ของ create expense ได้โดยไม่อ่านสคริปต์
- [ ] อธิบาย transaction/concurrency และยกตัวอย่าง race ได้
- [ ] รู้ว่า test แต่ละกลุ่มจับ regression อะไร
- [ ] เปิดระบบและรัน checks ได้เอง
- [ ] ซ้อม live change อย่างน้อยหนึ่งกรณีและตรวจ diff ของตัวเอง