# /zie-status improvements — test health detection

/zie-status ปัจจุบัน report test health เป็น "? stale" เสมอเพราะไม่ได้ detect .pytest_cache จริงๆ ทำให้ status block ไม่มีประโยชน์ในส่วนนี้

ปรับให้ detect last test run timestamp จาก .pytest_cache/v/cache/lastfailed และ compare กับ modified time ของ test files เพื่อ report ✓ pass / ✗ fail / ? stale ได้จริง
