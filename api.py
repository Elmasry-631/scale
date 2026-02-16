from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scale_reader import ScaleReader
import threading

app = FastAPI(title="Weighing Scale API")

# السماح بطلبات CORS (هام لجلب البيانات من واجهة Odoo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# إنشاء Instance واحدة فقط من ScaleReader
scale_reader = ScaleReader(port='COM5')

def start_reader():
    try:
        scale_reader.start()
    except Exception as exc:
        import traceback
        print("== Exception in ScaleReader Thread ==")
        traceback.print_exc()

# شغل Thread قراءة الميزان
reader_thread = threading.Thread(target=start_reader, daemon=True)
reader_thread.start()

@app.get("/api/weight")
def get_weight():
    """
    جلب آخر قراءة من الميزان Alfareed A2 كـ JSON.
    """
    data = scale_reader.get_latest_data()
    if data["weight"] is None:
        return {"error": "No data yet."}
    return data

@app.get("/api/health")
def health():
    """
    Endpoint للفحص السريع (هل الخدمة تعمل؟)
    """
    return {"status": "ok"}

# لتشغيل الخادم: uvicorn api:app --reload --host 0.0.0.0 --port 8000
