"""
Unified Fake Transfer Detector.
Routes input to the correct pipeline (screenshot or SMS) and returns
a standardized prediction with explanation.
"""

import os
import csv
from datetime import datetime

from .screenshot_pipeline import ScreenshotDetector
from .sms_pipeline import SMSDetector


class FakeTransferDetector:
    """
    Unified detection system for fake mobile money transfers.

    Accepts either:
      - Screenshot image → routed to Pipeline 1 (image forensics)
      - SMS text / CSV row → routed to Pipeline 2 (structural + NLP)

    Returns standardized prediction with XAI explanation.
    """

    def __init__(self, models_dir='models'):
        """
        Initialize both detection pipelines.

        Args:
            models_dir: Directory containing .pkl model files
        """
        screenshot_path = os.path.join(models_dir, 'pipeline1_screenshot_model.pkl')
        sms_path = os.path.join(models_dir, 'pipeline2_full_feature.pkl')

        # Load pipelines
        self.screenshot_detector = None
        self.sms_detector = None

        if os.path.exists(screenshot_path):
            self.screenshot_detector = ScreenshotDetector(screenshot_path)
            print(f"✅ Screenshot pipeline loaded: {self.screenshot_detector.model_name}")
        else:
            print(f"⚠️ Screenshot model not found at {screenshot_path}")

        if os.path.exists(sms_path):
            self.sms_detector = SMSDetector(sms_path)
            print(f"✅ SMS pipeline loaded: {self.sms_detector.model_name}")
        else:
            print(f"⚠️ SMS model not found at {sms_path}")

        # Logging
        self.log_file = os.path.join(os.path.dirname(models_dir), 'logs', 'detection_log.csv')
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def verify_transaction(self, input_data, input_type='auto'):
        """
        Verify whether a transaction is fake or genuine.

        Args:
            input_data: Either:
                - str: file path to screenshot image, OR SMS text
                - dict: CSV row with columns (bank, amount_ngn, balance_ngn,
                        date, time, description)
            input_type: 'image', 'text', or 'auto' (auto-detects)

        Returns:
            dict: {
                'prediction': 'FAKE' or 'GENUINE',
                'confidence': '87.5%',
                'reason': 'Human-readable explanation',
                'action': 'Recommended action for the vendor',
                'pipeline_used': 'screenshot' or 'sms',
                'timestamp': '2026-04-06 12:30:00'
            }
        """
        # Auto-detect input type
        if input_type == 'auto':
            if isinstance(input_data, str) and os.path.isfile(input_data):
                ext = os.path.splitext(input_data)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
                    input_type = 'image'
                else:
                    input_type = 'text'
            elif isinstance(input_data, dict):
                input_type = 'text'
            else:
                input_type = 'text'

        # Route to correct pipeline
        if input_type == 'image':
            if self.screenshot_detector is None:
                return {
                    'prediction': 'ERROR',
                    'confidence': '0%',
                    'reason': 'Screenshot detection model not loaded.',
                    'action': '⚠️ Please ensure pipeline1_screenshot_model.pkl is in the models/ folder.',
                    'pipeline_used': 'none',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            result = self.screenshot_detector.predict(input_data)
            result['pipeline_used'] = 'screenshot'

        else:  # text or structured data
            if self.sms_detector is None:
                return {
                    'prediction': 'ERROR',
                    'confidence': '0%',
                    'reason': 'SMS detection model not loaded.',
                    'action': '⚠️ Please ensure pipeline2_full_feature.pkl is in the models/ folder.',
                    'pipeline_used': 'none',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            result = self.sms_detector.predict(input_data)
            result['pipeline_used'] = 'sms'

        # Add timestamp
        result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log result
        self._log_result(input_data, input_type, result)

        return result

    def _log_result(self, input_data, input_type, result):
        """Log prediction to CSV file."""
        try:
            file_exists = os.path.exists(self.log_file)

            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                if not file_exists:
                    writer.writerow([
                        'timestamp', 'input_type', 'input_summary',
                        'prediction', 'confidence', 'reason', 'pipeline_used'
                    ])

                # Summarize input
                if input_type == 'image':
                    summary = str(input_data)[:100]
                elif isinstance(input_data, dict):
                    summary = str(input_data.get('description', ''))[:100]
                else:
                    summary = str(input_data)[:100]

                writer.writerow([
                    result.get('timestamp', ''),
                    input_type,
                    summary,
                    result.get('prediction', ''),
                    result.get('confidence', ''),
                    result.get('reason', ''),
                    result.get('pipeline_used', '')
                ])
        except Exception as e:
            pass  # Don't let logging errors break the prediction

    def get_model_info(self):
        """Return information about loaded models."""
        info = {}

        if self.screenshot_detector:
            info['screenshot'] = {
                'model': self.screenshot_detector.model_name,
                'features': self.screenshot_detector.selected_features,
                'metrics': self.screenshot_detector.metrics
            }

        if self.sms_detector:
            info['sms'] = {
                'model': self.sms_detector.model_name,
                'metrics': self.sms_detector.metrics
            }

        return info
