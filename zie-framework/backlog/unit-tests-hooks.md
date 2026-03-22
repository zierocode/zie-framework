# Add unit tests for all hooks (pytest)

hooks/*.py ทุกไฟล์ยังไม่มี unit tests เลย ทำให้ refactor ได้ยากและไม่รู้ว่า hook ทำงานถูกต้องไหมจนกว่าจะ run จริงใน Claude Code session

เขียน pytest tests ครอบ intent-detect.py, auto-test.py, safety-check.py, session-resume.py, session-learn.py, และ wip-checkpoint.py โดย mock stdin/stdout และ filesystem ที่จำเป็น เป้าหมายคือทุก hook มี test coverage ก่อนที่จะเพิ่ม feature ใหม่
