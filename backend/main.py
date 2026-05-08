import sys
import os

# Ensure project root is on sys.path before anything else
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.auth import router as auth_router
from backend.api.detect import router as detect_router
from backend.api.reports import router as reports_router

app = FastAPI(
    title="TransferNet",
    description="Explainable AI fraud detection for Nigerian SMEs",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,    prefix="/api/auth",    tags=["Authentication"])
app.include_router(detect_router,  prefix="/api/detect",  tags=["Detection"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])


@app.on_event("startup")
async def startup():
    from backend.core.detector_loader import get_detector, is_ready
    print("Loading ML models...")
    get_detector()
    status = "ready" if is_ready() else "unavailable"
    print(f"Detection model: {status}")


@app.get("/api/health")
def health():
    from backend.core.detector_loader import is_ready
    return {
        "status": "ok",
        "service": "TransferNet",
        "model_ready": is_ready(),
    }
