@echo off
echo Starting FastAPI server...
uvicorn api:app --reload --host 0.0.0.0 --port 8000
pause
