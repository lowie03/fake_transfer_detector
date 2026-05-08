"""
Core detection modules for Fake Transfer Detection System.
"""

from .detector import FakeTransferDetector
from .screenshot_pipeline import ScreenshotDetector, extract_template_features, BANK_TEMPLATES
from .sms_pipeline import SMSDetector
from .text_cleaning import clean_text, clean_sms_text, extract_text_structural_features
