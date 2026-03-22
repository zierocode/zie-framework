# Add skills/test-pyramid usage in /zie-build

/zie-build ปัจจุบัน invoke TDD loop โดยไม่ได้ใช้ test-pyramid skill เพื่อ guide ว่าควรเขียน test ระดับไหน (unit vs integration vs e2e) สำหรับ task นั้นๆ

เพิ่มให้ /zie-build invoke Skill(zie-framework:test-pyramid) ก่อนเริ่ม RED phase ของแต่ละ task เพื่อให้ Claude ตัดสินใจได้ว่าควรเขียน test ระดับไหนก่อน แทนที่จะ default เป็น unit test เสมอ
