"""
SMS/CSV Text Forgery Detection Pipeline.
Uses structured CSV features + TF-IDF + text structural features.
"""

import numpy as np
import pandas as pd
import re
import joblib
from scipy.sparse import hstack, csr_matrix

from .text_cleaning import clean_text, extract_text_structural_features


def extract_csv_features(row):
    """
    Extract features from all columns of a CSV/dict row.
    Works with both full CSV rows and text-only input.
    """
    features = {}
    description = str(row.get('description', '')) if pd.notna(row.get('description', '')) else ''

    # Amount & Balance
    try:
        amount = float(row.get('amount_ngn', 0)) if pd.notna(row.get('amount_ngn', 0)) else 0
    except:
        amount = 0
    try:
        balance = float(row.get('balance_ngn', 0)) if pd.notna(row.get('balance_ngn', 0)) else 0
    except:
        balance = 0

    features['amt_value'] = amount
    features['amt_log'] = np.log1p(amount)
    features['bal_value'] = balance
    features['bal_log'] = np.log1p(balance)
    features['amt_bal_ratio'] = (amount / balance) if balance > 0 else 0
    features['bal_minus_amt'] = balance - amount
    features['amt_is_round_1000'] = 1 if amount > 0 and amount % 1000 == 0 else 0
    features['amt_is_round_10000'] = 1 if amount > 0 and amount % 10000 == 0 else 0
    features['amt_gt_500k'] = 1 if amount > 500000 else 0
    features['amt_lt_1k'] = 1 if 0 < amount < 1000 else 0

    # Date
    date_str = str(row.get('date', '')) if pd.notna(row.get('date', '')) else ''
    features['date_has_comma'] = 1 if ',' in date_str else 0
    features['date_has_slash'] = 1 if '/' in date_str else 0
    features['date_has_dash'] = 1 if '-' in date_str else 0
    features['date_length'] = len(date_str)

    match = re.search(r'(202[0-9])', date_str)
    features['date_year'] = int(match.group(1)) if match else 0

    # Time
    time_str = str(row.get('time', '')) if pd.notna(row.get('time', '')) else ''
    features['time_is_missing'] = 1 if not time_str.strip() or time_str == 'nan' else 0

    # Extract hour
    hour = -1
    t = time_str.strip()
    if t and t != 'nan':
        m = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)?', t, re.IGNORECASE)
        if m:
            hour = int(m.group(1))
            ampm = m.group(3)
            if ampm:
                if ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif ampm.lower() == 'am' and hour == 12:
                    hour = 0
        else:
            m2 = re.match(r'(\d{1,2}):(\d{2})', t)
            if m2:
                hour = int(m2.group(1))

    features['time_hour'] = hour
    features['time_is_night'] = 1 if (hour >= 22 or (0 <= hour < 6)) else 0
    features['time_is_business'] = 1 if (9 <= hour <= 17) else 0

    # Bank
    bank = str(row.get('bank', 'unknown')) if pd.notna(row.get('bank', '')) else 'unknown'
    for b in ['GTBank', 'Zenith', 'Moniepoint']:
        features[f'bank_is_{b.lower()}'] = 1 if bank == b else 0

    # Account mask
    acct = str(row.get('account_masked', '')) if pd.notna(row.get('account_masked', '')) else ''
    features['acct_length'] = len(acct)
    features['acct_stars'] = acct.count('*')
    features['acct_starts_with_digit'] = 1 if acct and acct[0].isdigit() else 0

    # Description patterns
    features['desc_has_gtworld'] = 1 if 'GTWORLD' in description.upper() else 0
    features['desc_has_gtbank'] = 1 if 'GTBANK' in description.upper() else 0
    features['desc_has_credit_slash'] = 1 if 'CREDIT/' in description.upper() else 0
    features['desc_has_cip_cr'] = 1 if 'CIP CR' in description.upper() else 0
    features['desc_has_via'] = 1 if 'VIA' in description.upper() else 0
    features['desc_has_transfer'] = 1 if 'TRANSFER' in description.upper() else 0
    features['desc_has_reversed'] = 1 if 'REVERSED' in description.upper() else 0
    features['desc_has_nip'] = 1 if 'NIP' in description.upper() else 0
    features['desc_has_payment'] = 1 if 'PAYMENT' in description.upper() else 0
    features['desc_has_cashout'] = 1 if 'CASHOUT' in description.upper() else 0
    features['desc_has_rewards'] = 1 if 'REWARDS' in description.upper() else 0
    features['desc_length'] = len(description)
    features['desc_word_count'] = len(description.split()) if description else 0
    features['desc_upper_ratio'] = sum(c.isupper() for c in description) / max(len(description), 1)
    features['desc_has_slash'] = 1 if '/' in description else 0

    suspicious = ['cash prize', 'secure dept', 'admin office', 'revenue service',
                  'unknown sender', 'account verify', 'customer care', 'help desk']
    features['desc_has_suspicious_name'] = 1 if any(s in description.lower() for s in suspicious) else 0

    return features


class SMSDetector:
    """SMS/CSV forgery detection using structured + TF-IDF + text features."""

    def __init__(self, model_path):
        """Load the trained model package."""
        package = joblib.load(model_path)
        self.model = package['model_object']
        self.tfidf = package['tfidf_vectorizer']
        self.scaler_csv = package['scaler_csv']
        self.scaler_struct = package['scaler_struct']
        self.csv_feature_names = package['csv_feature_names']
        self.struct_feature_names = package['struct_feature_names']
        self.tfidf_feature_names = package['tfidf_feature_names']
        self.all_feature_names = package['all_feature_names']
        self.model_name = package['model_name']
        self.metrics = package.get('metrics_test', {})

    def predict(self, input_data):
        """
        Predict whether an SMS/transaction is forged and explain why.

        Args:
            input_data: Either a string (description text only) or a dict/Series
                       with full CSV columns (bank, amount, balance, date, time, description)

        Returns:
            dict with prediction, confidence, reason, action
        """
        # Handle string input (text only)
        if isinstance(input_data, str):
            row = {
                'bank': 'unknown', 'account_masked': '', 'amount_ngn': 0,
                'balance_ngn': 0, 'date': '', 'time': '', 'description': input_data
            }
        elif isinstance(input_data, pd.Series):
            row = input_data.to_dict()
        else:
            row = dict(input_data)

        description = str(row.get('description', '')) if pd.notna(row.get('description', '')) else ''

        # 1. CSV features
        csv_feats = extract_csv_features(row)
        csv_vec = np.array([[csv_feats.get(f, 0) for f in self.csv_feature_names]])
        csv_vec = np.nan_to_num(csv_vec, nan=0.0, posinf=0.0, neginf=0.0)
        csv_vec_scaled = self.scaler_csv.transform(csv_vec)

        # 2. Structural features
        struct_feats = extract_text_structural_features(description)
        struct_vec = np.array([[struct_feats.get(f, 0) for f in self.struct_feature_names]])
        struct_vec = np.nan_to_num(struct_vec, nan=0.0, posinf=0.0, neginf=0.0)
        struct_vec_scaled = self.scaler_struct.transform(struct_vec)

        # 3. TF-IDF features
        cleaned = clean_text(description) if description else 'empty'
        if not cleaned.strip():
            cleaned = 'empty'
        tfidf_vec = self.tfidf.transform([cleaned])

        # 4. Combine
        combined = hstack([tfidf_vec, csr_matrix(csv_vec_scaled), csr_matrix(struct_vec_scaled)])

        # 5. Predict
        prob = self.model.predict_proba(combined)[0][1]
        prediction = "FAKE" if prob >= 0.5 else "GENUINE"

        # 6. Build explanation
        reasons = []

        if csv_feats.get('desc_has_suspicious_name', 0):
            reasons.append("Suspicious sender name detected")
        if csv_feats.get('desc_has_gtbank', 0) and not csv_feats.get('desc_has_gtworld', 0):
            reasons.append("Uses 'GTBANK' instead of expected 'GTWORLD'")
        if csv_feats.get('desc_has_credit_slash', 0):
            reasons.append("'CREDIT/' prefix format detected")
        if csv_feats.get('desc_has_reversed', 0):
            reasons.append("Contains 'REVERSED' keyword")
        if csv_feats.get('amt_bal_ratio', 0) > 0.95:
            reasons.append(f"Amount nearly equals balance (ratio={csv_feats['amt_bal_ratio']:.2f})")
        if csv_feats.get('amt_is_round_10000', 0):
            reasons.append("Suspiciously round amount")
        if csv_feats.get('amt_gt_500k', 0):
            reasons.append("Unusually large amount (>500K NGN)")
        if csv_feats.get('date_has_dash', 0) and csv_feats.get('bank_is_gtbank', 0):
            reasons.append("Date format inconsistent with bank standard")
        if struct_feats.get('txt_field_count', 0) < 3:
            reasons.append(f"Incomplete message: {int(struct_feats.get('txt_field_count', 0))}/6 fields")

        if not reasons:
            reasons.append("Based on combined structural, text, and transaction analysis")

        return {
            'prediction': prediction,
            'confidence': f"{prob*100:.1f}%" if prediction == "FAKE" else f"{(1-prob)*100:.1f}%",
            'probability_fake': float(prob),
            'reason': f"{prediction}: " + "; ".join(reasons[:5]),
            'action': "⚠️ Do not trust this alert. Verify with your bank directly."
                      if prediction == "FAKE"
                      else "✅ Alert appears authentic. Standard verification applies."
        }
