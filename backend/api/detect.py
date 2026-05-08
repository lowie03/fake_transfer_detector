import os
import csv
import tempfile
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from backend.models.schemas import SMSDetectRequest, DetectionResult
from backend.core.detector_loader import get_detector
from backend.core.auth_service import get_user_by_token

router = APIRouter()

# Path to the detection log CSV — shared with reports.py
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_LOG_FILE = os.path.join(_PROJECT_ROOT, "fake_transfer_detector", "logs", "detection_log.csv")
_LOG_FIELDS = [
    "timestamp", "input_type", "prediction", "confidence",
    "risk_level", "reason", "pipeline_used",
]


def _require_token(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1]
    if not get_user_by_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")


def _parse_confidence(raw) -> float:
    """Convert whatever the model returns into a 0-100 float."""
    try:
        s = str(raw).strip().rstrip('%')
        val = float(s)
        # If it looks like a 0-1 fraction, scale to percentage
        if val <= 1.0:
            val = val * 100
        return round(val, 1)
    except (ValueError, TypeError):
        return 0.0


def _risk_level(confidence: float, prediction: str) -> str:
    pred = prediction.upper()
    if pred == "FAKE":
        if confidence >= 85:
            return "HIGH"
        if confidence >= 60:
            return "MEDIUM"
        return "LOW"
    return "SAFE"


def _log_detection(detection: DetectionResult):
    """Append a detection result to the CSV log file."""
    try:
        os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
        file_exists = os.path.exists(_LOG_FILE)
        with open(_LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_LOG_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "timestamp":    detection.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "input_type":   detection.pipeline,
                "prediction":   detection.prediction,
                "confidence":   detection.confidence,
                "risk_level":   detection.risk_level,
                "reason":       detection.explanation,
                "pipeline_used": detection.pipeline,
            })
    except Exception as e:
        # Logging failure should never break the API response
        print(f"[detect] Failed to log detection: {e}")


@router.post("/screenshot", response_model=DetectionResult)
async def predict_screenshot(
    file: UploadFile = File(...),
    bank: str = Form(default="unknown"),
    authorization: str | None = Header(default=None),
):
    _require_token(authorization)
    detector = get_detector()
    if detector is None:
        raise HTTPException(status_code=503, detail="Detection model is not available")

    suffix = os.path.splitext(file.filename or "upload.png")[1] or ".png"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = detector.verify_transaction(tmp_path, bank=bank, input_type="image")
        confidence_pct = _parse_confidence(result.get("confidence", 0))
        detection = DetectionResult(
            prediction=result.get("prediction", "UNKNOWN"),
            confidence=confidence_pct,
            explanation=result.get("reason", "Analysis complete."),
            action=result.get("action", ""),
            risk_level=_risk_level(confidence_pct, result.get("prediction", "")),
            pipeline=result.get("pipeline_used", "screenshot"),
            timestamp=result.get("timestamp", ""),
        )
        _log_detection(detection)
        return detection
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@router.post("/sms", response_model=DetectionResult)
def predict_sms(
    body: SMSDetectRequest,
    authorization: str | None = Header(default=None),
):
    _require_token(authorization)
    detector = get_detector()
    if detector is None:
        raise HTTPException(status_code=503, detail="Detection model is not available")

    has_extra = any([body.amount > 0, body.balance > 0, body.date, body.account, body.time])
    input_data = {
        "bank": body.bank,
        "account_masked": body.account,
        "amount_ngn": body.amount,
        "balance_ngn": body.balance,
        "date": body.date,
        "time": body.time,
        "description": body.text,
    } if has_extra else body.text

    try:
        result = detector.verify_transaction(input_data, bank=body.bank, input_type="text")
        confidence_pct = _parse_confidence(result.get("confidence", 0))
        detection = DetectionResult(
            prediction=result.get("prediction", "UNKNOWN"),
            confidence=confidence_pct,
            explanation=result.get("reason", "Analysis complete."),
            action=result.get("action", ""),
            risk_level=_risk_level(confidence_pct, result.get("prediction", "")),
            pipeline=result.get("pipeline_used", "sms"),
            timestamp=result.get("timestamp", ""),
        )
        _log_detection(detection)
        return detection
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
