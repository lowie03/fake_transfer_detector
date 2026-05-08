import os
import csv
from collections import defaultdict
from datetime import datetime
from io import StringIO
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from backend.core.auth_service import get_user_by_token

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_LOG_FILE = os.path.join(_PROJECT_ROOT, "fake_transfer_detector", "logs", "detection_log.csv")

router = APIRouter()


def _require_token(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    if not get_user_by_token(authorization.split(" ", 1)[1]):
        raise HTTPException(status_code=401, detail="Invalid token")


def _read_log() -> list[dict]:
    if not os.path.exists(_LOG_FILE):
        return []
    with open(_LOG_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _normalize_entry(row: dict) -> dict:
    pred = row.get("prediction", "UNKNOWN").upper()
    try:
        conf = round(float(row.get("confidence", 0)), 1)
        if conf <= 1.0:
            conf = round(conf * 100, 1)
    except (ValueError, TypeError):
        conf = None
    return {
        "timestamp":   row.get("timestamp", ""),
        "pipeline":    row.get("pipeline_used", row.get("input_type", "")),
        "prediction":  pred,
        "confidence":  conf,
        "risk_level":  row.get("risk_level", None),
        "explanation": row.get("reason", row.get("explanation", "")),
    }


@router.get("/stats")
def get_stats(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    rows = _read_log()
    total   = len(rows)
    fake    = sum(1 for r in rows if r.get("prediction", "").upper() == "FAKE")
    genuine = sum(1 for r in rows if r.get("prediction", "").upper() == "GENUINE")

    # daily counts for the last 7 days
    day_map: dict[str, int] = defaultdict(int)
    for r in rows:
        ts = r.get("timestamp", "")
        try:
            day = datetime.strptime(ts[:10], "%Y-%m-%d").strftime("%b %d")
            day_map[day] += 1
        except ValueError:
            pass
    daily_counts = [{"date": d, "count": c} for d, c in sorted(day_map.items())][-7:]

    # Average model confidence across all predictions
    confidences = []
    for r in rows:
        try:
            c = float(r.get("confidence", 0))
            if c <= 1.0:
                c = c * 100
            confidences.append(c)
        except (ValueError, TypeError):
            pass
    accuracy = round(sum(confidences) / len(confidences), 1) if confidences else 0

    return {
        "total":        total,
        "fake":         fake,
        "genuine":      genuine,
        "accuracy":     accuracy,
        "daily_counts": daily_counts,
        # legacy keys kept for compatibility
        "total_checks":    total,
        "fake_count":      fake,
        "genuine_count":   genuine,
        "fake_pct":        round(fake / total * 100, 1) if total else 0,
        "genuine_pct":     round(genuine / total * 100, 1) if total else 0,
    }


@router.get("/log")
def get_log(
    page: int = 1,
    limit: int = 10,
    authorization: str | None = Header(default=None),
):
    _require_token(authorization)
    rows = list(reversed(_read_log()))
    total = len(rows)
    start = (page - 1) * limit
    entries = [_normalize_entry(r) for r in rows[start: start + limit]]
    return {"total": total, "page": page, "limit": limit, "entries": entries}


@router.get("/export")
def export_csv(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    rows = _read_log()
    output = StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transfernet_log.csv"},
    )


@router.get("/model-info")
def model_info(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    from backend.core.detector_loader import get_detector
    detector = get_detector()
    if detector is None:
        return {"available": False}
    try:
        return {"available": True, "models": detector.get_model_info()}
    except Exception:
        return {"available": True, "models": {}}
