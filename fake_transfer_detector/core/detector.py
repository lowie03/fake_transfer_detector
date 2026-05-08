import os
from datetime import datetime
from .screenshot_pipeline import ScreenshotDetector
from .sms_pipeline import SMSDetector


class FakeTransferDetector:
    """
    Unified detection system.
    Routes input to Screenshot (image/PDF) or SMS (text) pipelines.

    Model path resolves relative to this file's location, so it works
    regardless of which directory uvicorn is started from.

    Expected layout:
      fake_transfer_detector/
        core/
          detector.py          ← this file
          screenshot_pipeline.py
          sms_pipeline.py
        models/
          pipeline1_receipt_model_v3.pkl
          pipeline2_sms_model_v2.pkl
    """

    SCREENSHOT_MODEL_FILENAME = 'pipeline1_receipt_model_v3.pkl'
    SMS_MODEL_FILENAME         = 'pipeline2_sms_model_v2.pkl'

    def __init__(self, models_dir=None):
        if models_dir is None:
            # Resolve models/ relative to THIS file, not the cwd.
            # os.path.dirname(__file__)        = fake_transfer_detector/core/
            # os.path.dirname(dirname(__file__))= fake_transfer_detector/
            models_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'models'
            )

        screenshot_path = os.path.join(models_dir, self.SCREENSHOT_MODEL_FILENAME)
        sms_path        = os.path.join(models_dir, self.SMS_MODEL_FILENAME)

        print(f"[Detector] Looking for models in: {models_dir}")

        # Screenshot pipeline
        if os.path.exists(screenshot_path):
            try:
                self.screenshot_detector = ScreenshotDetector(screenshot_path)
                print(f"[Detector] ✅ Screenshot model loaded")
            except Exception as e:
                print(f"[Detector] ❌ Screenshot model failed to load: {e}")
                self.screenshot_detector = None
        else:
            print(f"[Detector] ⚠️  Screenshot model not found: {screenshot_path}")
            self.screenshot_detector = None

        # SMS pipeline
        if os.path.exists(sms_path):
            try:
                self.sms_detector = SMSDetector(sms_path)
                print(f"[Detector] ✅ SMS model loaded")
            except Exception as e:
                print(f"[Detector] ❌ SMS model failed to load: {e}")
                self.sms_detector = None
        else:
            print(f"[Detector] ⚠️  SMS model not found: {sms_path}")
            self.sms_detector = None

    def verify_transaction(self, input_data, bank='unknown', input_type='auto'):
        """
        Route verification to the correct pipeline.

        Args:
            input_data:  File path for images/PDFs, or str/dict for SMS.
            bank:        'GTBank', 'Moniepoint', or 'Zenith' (exact match).
            input_type:  'image', 'sms', or 'auto' (default).
        """
        is_image = (
            input_type == 'image'
            or (
                isinstance(input_data, str)
                and input_data.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf'))
            )
        )

        if is_image:
            if not self.screenshot_detector:
                return self._error(
                    f"Screenshot model not loaded. "
                    f"Ensure {self.SCREENSHOT_MODEL_FILENAME} is in the models directory."
                )
            result = self.screenshot_detector.predict(input_data, bank=bank)
            result['pipeline_used'] = 'screenshot'

        else:
            if not self.sms_detector:
                return self._error(
                    f"SMS model not loaded. "
                    f"Ensure {self.SMS_MODEL_FILENAME} is in the models directory."
                )
            result = self.sms_detector.predict(input_data, bank=bank)
            result['pipeline_used'] = 'sms'

        result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return result

    def is_ready(self):
        """Return True if at least one pipeline is loaded."""
        return (
            self.screenshot_detector is not None
            or self.sms_detector is not None
        )

    def _error(self, message):
        return {
            'prediction':   'ERROR',
            'confidence':   '0%',
            'reason':       message,
            'action':       'Manual review required.',
            'pipeline_used':'none',
            'timestamp':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def get_model_info(self):
        """Return metadata for both pipelines."""
        info = {}
        if self.screenshot_detector:
            info['screenshot'] = self.screenshot_detector.get_model_info()
        else:
            info['screenshot'] = {
                'status': 'not loaded',
                'file':   self.SCREENSHOT_MODEL_FILENAME
            }
        if self.sms_detector:
            info['sms'] = self.sms_detector.get_model_info()
        else:
            info['sms'] = {
                'status': 'not loaded',
                'file':   self.SMS_MODEL_FILENAME
            }
        return info