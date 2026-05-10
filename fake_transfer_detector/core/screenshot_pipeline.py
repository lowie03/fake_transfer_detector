"""
Screenshot Forgery Detection Pipeline.
Compatible with pipeline1_receipt_model_v3.pkl
"""

import cv2
import numpy as np
import os
import joblib
import tempfile
import pytesseract

from .text_cleaning import extract_text_structural_features
from .explanations import build_screenshot_explanation

# Configure tesseract path for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


BANK_TEMPLATES = {
    'GTBank': {
        'required_keywords': [
            'receipt', 'success', 'sender', 'beneficiary',
            'receiver bank', 'receiver account', 'transaction type',
            'sessionid', 'remark'
        ],
        'status_keyword': 'success',
        'wrong_status':   ['successful', 'completed', 'done'],
        'expected_fields': [
            'sender', 'beneficiary', 'receiver bank',
            'receiver account', 'transaction type', 'sessionid'
        ],
        'amount_in_words': True,
        'has_disclaimer':  True,
        'disclaimer_keywords': ['subject to verification', 'fraud checks'],
        'branding': ['gtco', 'gtworld', 'gtbank'],
    },
    'Moniepoint': {
        'required_keywords': [
            'transaction type', 'transaction status', 'beneficiary',
            'sender name', 'source institution', 'transaction date',
            'transaction reference', 'provider reference'
        ],
        'status_keyword': 'successful',
        'wrong_status':   ['success', 'completed'],
        'expected_fields': [
            'transaction type', 'transaction status', 'beneficiary',
            'beneficiary institution', 'sender name', 'source institution',
            'transaction date', 'transaction reference'
        ],
        'amount_in_words': False,
        'has_disclaimer':  False,
        'branding': ['moniepoint', 'microfinance'],
        'ref_prefix': 'trf|',
    },
    'Zenith': {
        'required_keywords': [
            'transaction receipt', 'transaction type', 'transaction date',
            'debit account', 'credit account', 'beneficiary',
            'bank', 'narration', 'status', 'amount'
        ],
        'status_keyword': 'success',
        'wrong_status':   ['successful', 'completed'],
        'expected_fields': [
            'transaction type', 'transaction date', 'debit account',
            'credit account', 'beneficiary', 'bank',
            'narration', 'status', 'amount'
        ],
        'amount_in_words': False,
        'has_disclaimer':  True,
        'disclaimer_keywords': [
            'zenith bank confirmation', 'fraud proof verification',
            'zenithdirect@zenithbank.com'
        ],
        'branding': ['zenith'],
    }
}

ALWAYS_EXCLUDE = [
    'txt_total_chars', 'txt_total_words', 'txt_total_lines',
    'txt_avg_word_length', 'txt_space_ratio', 'txt_numeric_field_count',
    'img_sharpness_top_ratio', 'img_sharpness_mid_ratio',
    'img_sharpness_bot_ratio', 'img_sharpness_region_cv',
    'img_noise_region_cv', 'img_noise_max_min_ratio',
    'img_edge_region_cv', 'img_hist_entropy',
]


def convert_pdf_to_image(pdf_path):
    """Convert first PDF page to PNG. Tries PyMuPDF first, then pdf2image."""
    output_dir = tempfile.mkdtemp()

    # Method 1: PyMuPDF (no system dependency)
    try:
        import fitz
        doc  = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix  = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img_path = os.path.join(output_dir, 'converted.png')
        pix.save(img_path)
        doc.close()
        return img_path
    except ImportError:
        pass
    except Exception as e:
        print(f"[PDF] PyMuPDF failed: {e}")

    # Method 2: pdf2image (needs poppler)
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=200)
        if images:
            img_path = os.path.join(output_dir, 'converted.png')
            images[0].save(img_path, 'PNG')
            return img_path
    except Exception as e:
        print(f"[PDF] pdf2image failed: {e}")

    print("[PDF] All methods failed. Run: pip install PyMuPDF")
    return None


def extract_template_features(ocr_text, bank='unknown'):
    """Bank-specific structural template validation."""
    features   = {}
    text_lower = ocr_text.lower() if ocr_text else ''

    defaults = [
        'tpl_required_keywords_found', 'tpl_required_keywords_total',
        'tpl_required_keywords_ratio', 'tpl_expected_fields_found',
        'tpl_expected_fields_total', 'tpl_expected_fields_ratio',
        'tpl_status_correct', 'tpl_status_wrong',
        'tpl_has_amount_symbol', 'tpl_amount_in_words_present',
        'tpl_amount_in_words_expected', 'tpl_disclaimer_present',
        'tpl_disclaimer_expected', 'tpl_branding_present',
        'tpl_ref_format_correct', 'tpl_template_score',
        'tpl_missing_fields_count', 'tpl_field_completeness_pct',
    ]
    for d in defaults:
        features[d] = 0

    if not text_lower or bank == 'unknown':
        return features

    template = BANK_TEMPLATES.get(bank)
    if template is None:
        return features

    required     = template['required_keywords']
    found_kw     = sum(1 for kw in required if kw in text_lower)
    features['tpl_required_keywords_found'] = found_kw
    features['tpl_required_keywords_total'] = len(required)
    features['tpl_required_keywords_ratio'] = found_kw / len(required) if required else 0

    expected     = template['expected_fields']
    found_fields = sum(1 for f in expected if f in text_lower)
    missing      = len(expected) - found_fields
    features['tpl_expected_fields_found']  = found_fields
    features['tpl_expected_fields_total']  = len(expected)
    features['tpl_expected_fields_ratio']  = found_fields / len(expected) if expected else 0
    features['tpl_missing_fields_count']   = missing
    features['tpl_field_completeness_pct'] = (found_fields / len(expected) * 100) if expected else 0

    features['tpl_status_correct'] = int(template['status_keyword'] in text_lower)
    features['tpl_status_wrong']   = int(
        any(ws in text_lower for ws in template.get('wrong_status', []))
    )
    features['tpl_has_amount_symbol'] = int('₦' in ocr_text or 'ngn' in text_lower)

    features['tpl_amount_in_words_expected'] = int(bool(template.get('amount_in_words')))
    if template.get('amount_in_words'):
        number_words = [
            'one', 'two', 'three', 'four', 'five', 'six', 'seven',
            'eight', 'nine', 'ten', 'hundred', 'thousand', 'million',
            'naira', 'kobo', 'zero'
        ]
        features['tpl_amount_in_words_present'] = int(
            any(nw in text_lower for nw in number_words)
        )

    features['tpl_disclaimer_expected'] = int(bool(template.get('has_disclaimer')))
    if template.get('has_disclaimer'):
        features['tpl_disclaimer_present'] = int(
            any(dk in text_lower for dk in template.get('disclaimer_keywords', []))
        )

    features['tpl_branding_present'] = int(
        any(b in text_lower for b in template.get('branding', []))
    )

    if template.get('ref_prefix'):
        features['tpl_ref_format_correct'] = int(template['ref_prefix'] in text_lower)

    scores = [
        features['tpl_required_keywords_ratio'],
        features['tpl_expected_fields_ratio'],
        features['tpl_status_correct'],
        features['tpl_branding_present'],
    ]
    if features['tpl_disclaimer_expected']:
        scores.append(features['tpl_disclaimer_present'])
    if features['tpl_amount_in_words_expected']:
        scores.append(features['tpl_amount_in_words_present'])

    features['tpl_template_score'] = float(np.mean(scores)) if scores else 0.0
    return features


def _normalize_bank_name(bank):
    """Normalize frontend bank names to match BANK_TEMPLATES keys."""
    if not bank or bank == 'unknown':
        return 'unknown'
    bank_lower = bank.lower().strip()
    # Strip common suffixes
    for suffix in [' mfb', ' bank', ' plc', ' limited', ' ltd']:
        if bank_lower.endswith(suffix):
            bank_lower = bank_lower[:-len(suffix)].strip()
    # Map variations
    mapping = {
        'moniepoint': 'Moniepoint',
        'gtbank': 'GTBank',
        'gtb': 'GTBank',
        'zenith': 'Zenith',
    }
    return mapping.get(bank_lower, 'unknown')


def run_ocr(image_path):
    """OCR with preprocessing for better accuracy on receipt images.

    Uses grayscale directly (no binarization) because Otsu thresholding
    destroys text on colourful receipt backgrounds (Moniepoint blue,
    GTBank orange, etc.).
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Upscale small images
        h, w = gray.shape
        if h < 800 or w < 600:
            scale = max(800 / h, 600 / w)
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                              interpolation=cv2.INTER_CUBIC)

        # Mild contrast enhancement (CLAHE) — preserves colour backgrounds
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Try OCR on both normal grayscale and enhanced, pick the one with more text
        text_gray = pytesseract.image_to_string(gray)
        text_enhanced = pytesseract.image_to_string(enhanced)

        def count_alphanumeric(text):
            return sum(c.isalnum() for c in text)

        raw_text = text_enhanced if count_alphanumeric(text_enhanced) > count_alphanumeric(text_gray) else text_gray
        return raw_text.encode('utf-8', errors='replace').decode('utf-8')
    except Exception as e:
        print(f"[OCR] Error: {e}")
        return ""


class ScreenshotDetector:
    """
    Screenshot forgery detector.
    Compatible with pipeline1_receipt_model_v3.pkl
    """

    def __init__(self, model_path):
        package = joblib.load(model_path)

        self.model             = package['model_object']
        self.scaler            = package.get('scaler')
        self.selector          = package['feature_selector']
        self.selected_features = package['selected_features']
        self.model_name        = package['model_name']
        self.metrics           = package.get(
            'metrics_5fold', package.get('metrics_loocv', {})
        )
        self.all_safe_feature_names = package.get(
            'all_safe_feature_names',
            package.get('all_feature_names', [])
        )

        if not self.all_safe_feature_names:
            raise ValueError(
                "Model package missing feature names. "
                "Re-run Pipeline 1 notebook."
            )

    def predict(self, image_path, bank='unknown'):
        """
        Predict whether a receipt is forged.

        Args:
            image_path: Path to .jpg/.png or .pdf file.
            bank:       'GTBank', 'Moniepoint', or 'Zenith'.
        """
        original_path = image_path

        # PDF handling
        if isinstance(image_path, str) and image_path.lower().endswith('.pdf'):
            converted = convert_pdf_to_image(image_path)
            if converted is None:
                return self._error(
                    "Could not read this PDF. "
                    "Please take a screenshot of the receipt and upload that instead."
                )
            image_path = converted

        if not os.path.exists(image_path):
            return self._error(
                f"File not found: {os.path.basename(original_path)}"
            )

        img = cv2.imread(image_path)
        if img is None:
            return self._error(
                "Could not open this image file. "
                "Please ensure it is a valid JPG or PNG."
            )

        # OCR
        raw_text = run_ocr(image_path)
        
        if not raw_text.strip():
            return self._error(
                "Failed to extract readable text from this image. "
                "The image might be completely unreadable or the OCR engine failed."
            )

        # Normalize bank name from frontend (e.g. "Moniepoint MFB" → "Moniepoint")
        bank = _normalize_bank_name(bank)

        # DEBUG: Log the extracted text to a file so we can inspect it
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "ocr_debug.txt"), "a", encoding="utf-8") as f:
                f.write(f"\n--- OCR EXTRACTED FOR {bank} ---\n{raw_text}\n------------------\n")
        except Exception as e:
            print(f"Failed to write OCR debug log: {e}")

        # Features
        tpl_feats = extract_template_features(raw_text, bank)
        txt_feats = extract_text_structural_features(raw_text)
        all_feats = {**tpl_feats, **txt_feats}

        safe_names = [
            f for f in self.all_safe_feature_names
            if f not in ALWAYS_EXCLUDE
        ]
        vec = np.array([[all_feats.get(f, 0) for f in safe_names]])
        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)

        vec_selected = self.selector.transform(vec)
        if self.scaler is not None:
            vec_selected = self.scaler.transform(vec_selected)

        prob       = self.model.predict_proba(vec_selected)[0][1]
        prediction = "FAKE" if prob >= 0.5 else "GENUINE"
        confidence = prob if prediction == "FAKE" else (1 - prob)

        # Plain-language explanation
        reasons = build_screenshot_explanation(
            tpl_feats, txt_feats, bank, prediction, raw_text=raw_text
        )

        # XAI Insights
        xai_insights = self._extract_xai(vec_selected)

        return {
            'prediction':             prediction,
            'confidence':             f"{confidence * 100:.1f}%",
            'probability_fake':       float(prob),
            'reason':                 "; ".join(reasons),
            'reasons_list':           reasons,
            'xai_insights':           xai_insights,
            'action': (
                "Do not confirm this payment. "
                "Call your bank directly to verify the transaction."
                if prediction == "FAKE"
                else
                "This receipt looks genuine. "
                "You may proceed, but always confirm large payments with your bank."
            ),
            'ocr_text':               raw_text,
            'bank':                   bank,
            'template_score':         float(tpl_feats.get('tpl_template_score', 0)),
            'field_completeness_pct': float(tpl_feats.get('tpl_field_completeness_pct', 0)),
        }

    def _extract_xai(self, vec_selected):
        try:
            coefs = self.model.coef_[0]
            features = vec_selected[0]
            contributions = features * coefs
            
            insights = []
            for name, contrib in zip(self.selected_features, contributions):
                if abs(contrib) < 0.1:
                    continue
                    
                hr_name = name.replace('_', ' ').title()
                if 'Tpl Missing Fields' in hr_name: hr_name = "Missing expected bank fields"
                elif 'Txt Garbled' in hr_name: hr_name = "Unreadable/corrupted text (OCR)"
                elif 'Txt Field Count' in hr_name: hr_name = "Lack of readable structural fields"
                elif 'Tpl Required Keywords Ratio' in hr_name: hr_name = "Missing mandatory keywords"
                elif 'Tpl Branding Present' in hr_name: hr_name = "Bank branding/logo detection"
                elif 'Tpl Status Correct' in hr_name: hr_name = "Transaction status wording"
                elif 'Tpl Template Score' in hr_name: hr_name = "Overall layout conformity"
                
                insights.append({
                    'feature': hr_name,
                    'contribution': float(contrib),
                    'type': 'FAKE' if contrib > 0 else 'GENUINE'
                })
            
            insights.sort(key=lambda x: abs(x['contribution']), reverse=True)
            return insights[:4]
        except Exception as e:
            print(f"[XAI] Error extracting XAI: {e}")
            return []

    def _error(self, message):
        return {
            'prediction':         'ERROR',
            'confidence':         '0%',
            'reason':             message,
            'reasons_list':       [message],
            'xai_insights':       [],
            'action':             'Please check the file and try again.',
            'ocr_text':           '',
        }

    def get_model_info(self):
        return {
            'pipeline':          'Receipt Forgery Detection v3',
            'model_name':        self.model_name,
            'selected_features': self.selected_features,
            'metrics':           self.metrics,
        }