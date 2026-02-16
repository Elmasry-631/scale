"""HTTP API layer for exposing serial scale readings."""

import logging
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scale_reader import ScaleReader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_origins(value: str):
    """Convert comma-separated origins env var to a list."""
    if not value:
        return ["*"]
    return [origin.strip() for origin in value.split(",") if origin.strip()]


SCALE_PORT = os.getenv("SCALE_PORT", "COM5")
SCALE_BAUDRATE = int(os.getenv("SCALE_BAUDRATE", "9600"))
SCALE_TIMEOUT = float(os.getenv("SCALE_TIMEOUT", "1"))
CORS_ORIGINS = _parse_origins(os.getenv("CORS_ORIGINS", "*"))

app = FastAPI(title="Weighing Scale API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

scale_reader = ScaleReader(
    port=SCALE_PORT,
    baudrate=SCALE_BAUDRATE,
    timeout=SCALE_TIMEOUT,
)


class WeightResponse(BaseModel):
    weight: float
    unit: str
    timestamp: str


class WeightPendingResponse(BaseModel):
    error: str


class HealthResponse(BaseModel):
    status: str
    running: bool
    serial_connected: bool
    port: str
    last_timestamp: Optional[str] = None
    last_error: Optional[str] = None


@app.on_event("startup")
def on_startup():
    """Start background reader when API process starts."""
    logger.info("Starting ScaleReader")
    scale_reader.start()


@app.on_event("shutdown")
def on_shutdown():
    """Stop background reader when API process is shutting down."""
    logger.info("Stopping ScaleReader")
    scale_reader.stop()


@app.get(
    "/api/weight",
    response_model=WeightResponse | WeightPendingResponse,
    summary="Get latest scale reading",
    description="Returns latest parsed weight from the serial scale, or pending error if no sample yet.",
)
def get_weight():
    """جلب آخر قراءة من الميزان Alfareed A2 كـ JSON."""
    data = scale_reader.get_latest_data()
    if data["weight"] is None:
        return {"error": "No data yet."}
    return data


@app.get(
    "/api/health",
    response_model=HealthResponse,
    summary="Health and diagnostics",
    description="Reports service state, serial connection status, last sample timestamp, and last error.",
)
def health():
    """Endpoint للفحص السريع (هل الخدمة تعمل؟)."""
    status = scale_reader.get_status()
    return {
        "status": "ok",
        **status,
    }


# لتشغيل الخادم: uvicorn api:app --reload --host 0.0.0.0 --port 8000
