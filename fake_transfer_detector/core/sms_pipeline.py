import numpy as np
import pandas as pd
import re
import joblib
from scipy.sparse import hstack, csr_matrix
from .text_cleaning import clean_sms_text, extract_text_structural_features
from .explanations import build_sms_explanation

SMS_TEMPLATES = {
    'GTBank': {
        'required_keywords': ['acct:', 'amt:', 'ngn', 'cr', 'desc:', 'avail bal:', 'date:'],
        'format_patterns': {
            'date_format':    r'\d{4}-\d{2}-\d{2}',
            'amount_format':  r'ngn[\d,]+\.\d{2}\s*cr',
            'balance_format': r'avail bal:\s*ngn',
            'account_format': r'\*{6}\d{4}',
        },
        'description_keywords': ['webappwork', 'being payment', 'via gtworld'],
        'status_keyword': None,
        'footer': None,
    },
    'Zenith': {
        'required_keywords': ['acct:', 'dt:', 'cr amt:', 'bal:'],
        'format_patterns': {
            'date_format':    r'\d{2}/\d{2}/\d{4}',
            'amount_format':  r'cr amt:\s*[\d,]+\.\d{2}',
            'balance_format': r'bal:\s*[\d,]+\.\d{2}',
            'account_format': r'\d{3}\*{4}\d{3}',
        },
        'description_keywords': ['cip cr/', 'nip/', 'dial *966#'],
        'footer': 'dial *966#',
    },
    'Moniepoint': {
        'required_keywords': ['credit alert', 'acc:', 'amt:', 'ngn', 'bal:', 'date:', 'time:', 'desc:'],
        'format_patterns': {
            'date_format':    r'[a-z]{3},\s*\d{2}\s+[a-z]+\s+\d{4}',
            'amount_format':  r'amt:\s*ngn[\d,]+\.\d{2}',
            'balance_format': r'bal:\s*ngn[\d,]+\.\d{2}',
            'account_format': r'\d{3}\*{4}\d{3}',
        },
        'description_keywords': ['trf frm', 'credit alert'],
        'header': 'credit alert',
    }
}

# Features zeroed at inference time — they perfectly separated fake/genuine
# in training only because fake data was generated without correct date formats.
SMS_LEAKY_BLACKLIST = [
    'sms_tpl_date_format_valid',
    'sms_tpl_format_checks_passed',
    'sms_tpl_header_present',
    'sms_tpl_footer_present',
    'meta_date_has_dash',
    'meta_date_has_comma',
    'meta_date_has_slash',
    'meta_date_length',
]


def extract_sms_template_features(sms_text, bank='unknown'):
    """Validate SMS text against bank-specific template rules."""
    features = {
        'sms_tpl_keywords_found':       0,
        'sms_tpl_keywords_total':       0,
        'sms_tpl_keywords_ratio':       0,
        'sms_tpl_date_format_valid':    0,
        'sms_tpl_amount_format_valid':  0,
        'sms_tpl_balance_format_valid': 0,
        'sms_tpl_account_format_valid': 0,
        'sms_tpl_desc_keyword_found':   0,
        'sms_tpl_footer_present':       0,
        'sms_tpl_header_present':       0,
        'sms_tpl_template_score':       0,
        'sms_tpl_format_checks_passed': 0,
        'sms_tpl_format_checks_total':  4,
    }

    text_lower = sms_text.lower() if isinstance(sms_text, str) else ''
    if not text_lower or bank == 'unknown':
        return features

    template = SMS_TEMPLATES.get(bank)
    if template is None:
        return features

    required  = template['required_keywords']
    found     = sum(1 for kw in required if kw in text_lower)
    features['sms_tpl_keywords_found'] = found
    features['sms_tpl_keywords_total'] = len(required)
    features['sms_tpl_keywords_ratio'] = found / len(required) if required else 0

    patterns      = template.get('format_patterns', {})
    checks_passed = 0
    for key, feat_key in [
        ('date_format',    'sms_tpl_date_format_valid'),
        ('amount_format',  'sms_tpl_amount_format_valid'),
        ('balance_format', 'sms_tpl_balance_format_valid'),
        ('account_format', 'sms_tpl_account_format_valid'),
    ]:
        if key in patterns:
            match = 1 if re.search(patterns[key], text_lower) else 0
            features[feat_key] = match
            checks_passed += match

    features['sms_tpl_format_checks_passed'] = checks_passed

    desc_kws = template.get('description_keywords', [])
    features['sms_tpl_desc_keyword_found'] = int(
        any(dk in text_lower for dk in desc_kws)
    )

    if template.get('footer'):
        features['sms_tpl_footer_present'] = int(template['footer'] in text_lower)
    if template.get('header'):
        features['sms_tpl_header_present'] = int(template['header'] in text_lower)

    scores = [
        features['sms_tpl_keywords_ratio'],
        checks_passed / 4,
        features['sms_tpl_desc_keyword_found'],
    ]
    features['sms_tpl_template_score'] = float(np.mean(scores))

    return features


def extract_sms_metadata_features(row):
    """Extract structural and metadata features from a CSV row or dict."""
    features   = {}
    sms_text   = str(row.get('description', '')) if pd.notna(row.get('description', '')) else ''
    text_lower = sms_text.lower()

    def safe_float(val):
        try:
            return float(val) if pd.notna(val) else 0.0
        except (ValueError, TypeError):
            return 0.0

    amount  = safe_float(row.get('amount_ngn', 0))
    balance = safe_float(row.get('balance_ngn', 0))

    features['meta_amount']             = amount
    features['meta_amount_log']         = np.log1p(amount)
    features['meta_balance']            = balance
    features['meta_balance_log']        = np.log1p(balance)
    features['meta_amt_bal_ratio']      = (amount / balance) if balance > 0 else 0
    features['meta_bal_minus_amt']      = balance - amount
    features['meta_amt_is_round_1000']  = int(amount > 0 and amount % 1000 == 0)
    features['meta_amt_is_round_10000'] = int(amount > 0 and amount % 10000 == 0)
    features['meta_amt_gt_500k']        = int(amount > 500000)

    date_str = str(row.get('date', '')) if pd.notna(row.get('date', '')) else ''
    features['meta_date_has_slash']  = int('/' in date_str)
    features['meta_date_has_dash']   = int('-' in date_str)
    features['meta_date_has_comma']  = int(',' in date_str)
    features['meta_date_length']     = len(date_str)

    time_str = str(row.get('time', '')) if pd.notna(row.get('time', '')) else ''
    features['meta_time_missing'] = int(not time_str.strip() or time_str == 'nan')

    hour = -1
    if time_str.strip() and time_str != 'nan':
        m = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str, re.IGNORECASE)
        if m:
            hour = int(m.group(1))
            ampm = m.group(3)
            if ampm:
                if ampm.lower() == 'pm' and hour != 12: hour += 12
                elif ampm.lower() == 'am' and hour == 12: hour = 0
    features['meta_time_hour']     = hour
    features['meta_time_is_night'] = int(hour >= 22 or (0 <= hour < 6))

    bank = str(row.get('bank', 'unknown')) if pd.notna(row.get('bank', '')) else 'unknown'
    for b in ['GTBank', 'Zenith', 'Moniepoint']:
        features[f'meta_bank_is_{b.lower()}'] = int(bank == b)

    acct = str(row.get('account_masked', '')) if pd.notna(row.get('account_masked', '')) else ''
    features['meta_acct_length']       = len(acct)
    features['meta_acct_stars']        = acct.count('*')
    features['meta_acct_starts_digit'] = int(bool(acct) and acct[0].isdigit())

    features['meta_has_gtworld']        = int('gtworld' in text_lower)
    features['meta_has_gtbank']         = int('gtbank' in text_lower and 'gtworld' not in text_lower)
    features['meta_has_webappwork']     = int('webappwork' in text_lower)
    features['meta_has_being_payment']  = int('being payment' in text_lower)
    features['meta_has_credit_slash']   = int('credit/' in text_lower)
    features['meta_has_cip_cr']         = int('cip cr' in text_lower)
    features['meta_has_credit_alert']   = int('credit alert' in text_lower)
    features['meta_has_trf_frm']        = int('trf frm' in text_lower)
    features['meta_has_transfer']       = int('transfer' in text_lower)
    features['meta_has_nip']            = int('nip/' in text_lower)
    features['meta_has_dial_966']       = int('dial *966' in text_lower or '*966#' in text_lower)
    features['meta_has_avail_bal']      = int('avail bal' in text_lower)

    suspicious_phrases = [
        'click here', 'verify account', 'pending verification',
        'confirm account', 'update details', 'suspend',
        'expire', 'click link', 'www.', 'http'
    ]
    features['meta_has_suspicious_phrase'] = int(
        any(s in text_lower for s in suspicious_phrases)
    )

    suspicious_names = [
        'cash prize', 'secure dept', 'admin office', 'revenue service',
        'unknown sender', 'account verify', 'customer care', 'help desk',
        'lottery', 'claims dept', 'prize commission'
    ]
    features['meta_has_suspicious_name'] = int(
        any(s in text_lower for s in suspicious_names)
    )

    lines = sms_text.split('\n')
    features['meta_line_count']  = len(lines)
    features['meta_char_count']  = len(sms_text)
    features['meta_word_count']  = len(sms_text.split())

    field_indicators = [
        'acct', 'acc:', 'amt:', 'bal:', 'date:', 'time:',
        'desc:', 'dt:', 'cr amt:', 'avail bal:'
    ]
    present = sum(1 for f in field_indicators if f in text_lower)
    features['meta_fields_present']       = present
    features['meta_fields_present_ratio'] = present / 10

    return features


class SMSDetector:
    """
    SMS transaction alert fraud detector.
    Compatible with pipeline2_sms_model_v2.pkl
    Labels: 1 = GENUINE, 0 = FAKE
    """

    def __init__(self, model_path):
        package = joblib.load(model_path)

        self.model               = package['model_object']
        self.tfidf               = package.get('tfidf_vectorizer')
        self.scaler_tpl          = package.get('scaler_tpl')
        self.scaler_meta         = package.get('scaler_meta')
        self.tpl_feature_names   = package.get('tpl_feature_names', [])
        self.meta_feature_names  = package.get('meta_feature_names', [])
        self.tfidf_feature_names = package.get('tfidf_feature_names', [])
        self.all_feature_names   = package.get('all_feature_names', [])
        self.sms_templates       = package.get('sms_templates', SMS_TEMPLATES)
        self.metrics             = package.get('metrics_5fold', {})

        missing = [k for k in ['tfidf_vectorizer', 'scaler_tpl', 'scaler_meta']
                   if package.get(k) is None]
        if missing:
            raise ValueError(
                f"SMS model package missing keys: {missing}. "
                "Re-run Pipeline 2 notebook."
            )

    def _build_vector(self, sms_text, bank, row):
        tpl_feats  = extract_sms_template_features(sms_text, bank)
        meta_feats = extract_sms_metadata_features(row)

        # Zero leaky features
        for feat in SMS_LEAKY_BLACKLIST:
            if feat in tpl_feats:  tpl_feats[feat]  = 0
            if feat in meta_feats: meta_feats[feat] = 0

        cleaned = clean_sms_text(sms_text)
        if not cleaned.strip():
            cleaned = 'empty'

        tpl_vec  = np.array([[tpl_feats.get(f, 0)  for f in self.tpl_feature_names]])
        meta_vec = np.array([[meta_feats.get(f, 0) for f in self.meta_feature_names]])
        tpl_vec  = np.nan_to_num(tpl_vec,  nan=0.0)
        meta_vec = np.nan_to_num(meta_vec, nan=0.0)

        tpl_scaled  = self.scaler_tpl.transform(tpl_vec)
        meta_scaled = self.scaler_meta.transform(meta_vec)
        tfidf_vec   = self.tfidf.transform([cleaned])

        combined = hstack([tfidf_vec, csr_matrix(tpl_scaled), csr_matrix(meta_scaled)])
        return combined, tpl_feats, meta_feats

    def predict(self, input_data, bank='unknown'):
        """
        Predict and explain whether an SMS alert is fraudulent.

        Args:
            input_data: SMS text string, or dict/pd.Series with CSV columns.
            bank:       'GTBank', 'Moniepoint', or 'Zenith'.
        """
        if isinstance(input_data, str):
            row = {
                'bank': bank, 'account_masked': '', 'amount_ngn': 0,
                'balance_ngn': 0, 'date': '', 'time': '',
                'description': input_data, 'sms_text': input_data,
            }
        elif isinstance(input_data, pd.Series):
            row = input_data.to_dict()
        else:
            row = dict(input_data)

        if 'sms_text' not in row:
            row['sms_text'] = row.get('description', '')

        sms_text = str(row.get('sms_text', '')) if pd.notna(row.get('sms_text', '')) else ''
        bank     = str(row.get('bank', bank))

        combined, tpl_feats, meta_feats = self._build_vector(sms_text, bank, row)

        prob_genuine = self.model.predict_proba(combined)[0][1]
        prob_fake    = 1 - prob_genuine
        prediction   = "GENUINE" if prob_genuine >= 0.5 else "FAKE"
        confidence   = prob_fake if prediction == "FAKE" else prob_genuine

        reasons = build_sms_explanation(tpl_feats, meta_feats, bank, prediction, sms_text=sms_text)
        
        # XAI Insights
        xai_insights = self._extract_xai(combined)

        return {
            'prediction':       prediction,
            'confidence':       f"{confidence * 100:.1f}%",
            'probability_fake': float(prob_fake),
            'reason':           "; ".join(reasons),
            'reasons_list':     reasons,
            'xai_insights':     xai_insights,
            'action': (
                "Do not accept this payment. "
                "Contact your bank directly to verify the transaction."
                if prediction == "FAKE"
                else
                "This alert looks genuine. "
                "Always verify large transactions through your bank's official app."
            ),
            'bank':             bank,
            'template_score':   float(tpl_feats.get('sms_tpl_template_score', 0)),
        }

    def _extract_xai(self, combined_vec):
        try:
            coefs = self.model.coef_[0]
            features = combined_vec.toarray()[0] if hasattr(combined_vec, 'toarray') else combined_vec[0]
            contributions = features * coefs
            
            insights = []
            for name, contrib in zip(self.all_feature_names, contributions):
                if abs(contrib) < 0.1:
                    continue
                    
                hr_name = name.replace('_', ' ').title()
                if 'Tpl Keywords' in hr_name: hr_name = "Presence of mandatory keywords"
                elif 'Format Checks' in hr_name: hr_name = "Text format conformity"
                elif 'Meta Has Suspicious Phrase' in hr_name: hr_name = "Suspicious phishing phrases"
                elif 'Meta Amt Bal Ratio' in hr_name: hr_name = "Amount/Balance mathematical logic"
                elif 'Tpl Desc Keyword' in hr_name: hr_name = "Bank-specific description format"
                elif 'Meta Date Has' in hr_name: hr_name = "Date punctuation format"
                
                insights.append({
                    'feature': hr_name,
                    'contribution': float(contrib),
                    'type': 'FAKE' if contrib < 0 else 'GENUINE' # In SMS: 1=GENUINE, 0=FAKE. So negative pushed towards FAKE.
                })
            
            # Since 1=GENUINE, 0=FAKE in SMS model: 
            # Negative log-odds contribution means the model was pushed towards FAKE (Class 0).
            # Positive log-odds contribution means pushed towards GENUINE (Class 1).
            # We already mapped 'type' based on this. Now we sort by absolute contribution.
            insights.sort(key=lambda x: abs(x['contribution']), reverse=True)
            return insights[:4]
        except Exception as e:
            print(f"[XAI] Error extracting SMS XAI: {e}")
            return []

    def get_model_info(self):
        return {
            'pipeline':       'SMS Fraud Detection v2',
            'tpl_features':   len(self.tpl_feature_names),
            'meta_features':  len(self.meta_feature_names),
            'tfidf_features': len(self.tfidf_feature_names),
            'metrics':        self.metrics,
        }