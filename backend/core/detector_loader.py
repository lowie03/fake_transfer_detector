import sys
import os

# Insert project root (parent of backend/) so fake_transfer_detector is importable
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_MODELS_DIR = os.path.join(_PROJECT_ROOT, "fake_transfer_detector", "models")

try:
    from fake_transfer_detector.core.detector import FakeTransferDetector
    _DETECTOR_AVAILABLE = True
except Exception as _e:
    print(f"[detector_loader] Could not import FakeTransferDetector: {_e}")
    _DETECTOR_AVAILABLE = False

_detector = None


def get_detector():
    global _detector
    if not _DETECTOR_AVAILABLE:
        return None
    if _detector is None:
        _detector = FakeTransferDetector(models_dir=_MODELS_DIR)
    return _detector


def is_ready() -> bool:
    try:
        d = get_detector()
        return d is not None
    except Exception:
        return False
