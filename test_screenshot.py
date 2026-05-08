"""Quick test: does the screenshot model give different predictions for different inputs?"""

from fake_transfer_detector.core.screenshot_pipeline import (
    ScreenshotDetector, extract_template_features, ALWAYS_EXCLUDE
)
from fake_transfer_detector.core.text_cleaning import extract_text_structural_features
import numpy as np

det = ScreenshotDetector('fake_transfer_detector/models/pipeline1_receipt_model_v3.pkl')
safe_names = [f for f in det.all_safe_feature_names if f not in ALWAYS_EXCLUDE]

def predict_text(text, bank):
    tpl = extract_template_features(text, bank)
    txt = extract_text_structural_features(text)
    all_f = {**tpl, **txt}
    vec = np.array([[all_f.get(f, 0) for f in safe_names]])
    vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
    vec_sel = det.selector.transform(vec)
    if det.scaler:
        vec_sel = det.scaler.transform(vec_sel)
    prob = det.model.predict_proba(vec_sel)[0][1]
    pred = "FAKE" if prob >= 0.5 else "GENUINE"
    conf = prob if pred == "FAKE" else (1 - prob)
    print(f"\n--- bank={bank} ---")
    print(f"  prob_fake={prob:.4f}  prediction={pred}  confidence={conf*100:.1f}%")
    print(f"  tpl_score={tpl.get('tpl_template_score',0):.3f}")
    print(f"  field_completeness={tpl.get('tpl_field_completeness_pct',0):.1f}%")
    print(f"  keywords_ratio={tpl.get('tpl_required_keywords_ratio',0):.3f}")
    print(f"  branding={tpl.get('tpl_branding_present',0)}")
    print(f"  txt_field_count={txt.get('txt_field_count',0)}")
    print(f"  txt_ocr_confidence_proxy={txt.get('txt_ocr_confidence_proxy',0):.3f}")

# Test 1: Genuine GTBank receipt text
gtbank_text = """Receipt Success Sender John Doe Beneficiary Jane Smith
Receiver Bank Zenith Receiver Account 1234567890
Transaction Type Transfer SessionID MFDS12345 Remark Payment
Subject to verification fraud checks GTWorld NGN 50,000.00"""
predict_text(gtbank_text, 'GTBank')

# Test 2: Minimal/empty text with unknown bank (simulates OCR failure)
predict_text("random stuff hello world", 'unknown')

# Test 3: Moniepoint receipt text
moniepoint_text = """Transaction Type Credit Transaction Status Successful
Beneficiary Jane Smith Sender Name John Doe Source Institution GTBank
Transaction Date 2024-01-15 Transaction Reference TRF123456
Provider Reference PR789 Moniepoint NGN 25,000.00"""
predict_text(moniepoint_text, 'Moniepoint')

# Test 4: Empty string (simulates total OCR failure)
predict_text("", 'GTBank')
