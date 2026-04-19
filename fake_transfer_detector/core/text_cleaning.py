"""
Text cleaning and structural feature extraction utilities.
Shared between both pipelines.
"""

import re
import numpy as np
import pandas as pd


def clean_text(text):
    """
    Aggressive multi-pass cleaning for fraud detection text.
    Removes transaction IDs, PII names, phone numbers, normalizes
    currency and bank names, strips UI noise.
    """
    if not isinstance(text, str) or not text:
        return ""

    text = text.lower()

    # PASS 1: Remove Transaction IDs
    text = re.sub(r'\bmfds[a-z0-9]+\b', ' ', text)
    text = re.sub(r'\b(?=[a-z0-9]*[a-z])(?=[a-z0-9]*\d)[a-z0-9]{12,}\b', ' ', text)
    text = re.sub(r'\b[a-z]{2,}\d{8,}[a-z]{0,6}\b', ' ', text)
    text = re.sub(r'\b[a-z0-9]{6,}[/\-][a-z0-9]{3,}\b', ' ', text)
    text = re.sub(r'\b\d{8,}\b', ' ', text)

    # PASS 2: Remove PII Names
    _NAMES = "chidi eze emeka nwosu tunde afolabi okoro okon obi godwin martins okafor daniel umar victor edward john paul david divine praise blessing adeyemi amaka justina tochukwu grace eneh hansen ehinomeh olanipekun foko gabzy renee consort sarah victoria kemi adewale ifeanyi chukwu ada umeh"
    for name in _NAMES.split():
        text = re.sub(r'\b' + name + r'\b', ' ', text)

    # PASS 3: Remove Phone Numbers
    text = re.sub(r'\b(?:070|080|081|090|091)\d{8}\b', ' ', text)
    text = re.sub(r'\+?234\d{10}\b', ' ', text)
    text = re.sub(r'\b\d{10,}\b', ' ', text)

    # PASS 4: Normalize Transaction Types & Currency
    text = re.sub(r'\b(?:nip|trf|cip|ach|pos)\s?[/\\]\s?', ' transaction_type ', text)
    text = re.sub(r'\b(?:cr|dr)\s?[/\\]', ' transaction_type ', text)
    text = re.sub(r'\b(?:ngn|₦|n)\s?[\d,]+(?:\.\d+)?\b', ' currency_amount ', text)
    text = re.sub(r'\b[\d,]+\.?\d*\s?(?:naira|kobo)\b', ' currency_amount ', text)
    text = re.sub(r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b', ' currency_amount ', text)

    bank_map = {
        'gtworld': 'gtbank', 'gtb': 'gtbank',
        'firstbank': 'firstbank', 'first bank': 'firstbank',
        'zzenith': 'zenithbank', 'zenith': 'zenithbank',
        'moniepoint': 'moniepoint', 'opay': 'opay',
        'kuda': 'kuda', 'palmpay': 'palmpay',
        'access': 'accessbank', 'fcmb': 'fcmb', 'uba': 'uba',
    }
    for wrong, right in bank_map.items():
        text = re.sub(r'\b' + re.escape(wrong) + r'\b', right, text)

    # PASS 5: Remove UI Noise
    ui_noise = ['battery', 'wifi', 'lte', 'png', 'jpg', 'gmt',
                'screenshot', 'download', 'qr', 'app', 'www', 'com', 'http', 'https']
    for noise in ui_noise:
        text = re.sub(r'\b' + re.escape(noise) + r'\b', ' ', text)
    text = re.sub(r'\b\d+%', ' ', text)
    text = re.sub(r'\b\d{1,2}:\d{2}\s?(?:am|pm)?\b', ' ', text)

    # PASS 6: Final Cleanup
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\b[a-z]\b', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_text_structural_features(raw_text, bank='unknown'):
    """
    Extract STRUCTURAL features from text — not what it SAYS but HOW it's structured.
    Used by both screenshot and SMS pipelines.
    """
    features = {}

    if not isinstance(raw_text, str) or not raw_text:
        for key in ['txt_total_chars', 'txt_total_words', 'txt_total_lines',
                     'txt_avg_word_length', 'txt_digit_ratio', 'txt_upper_ratio',
                     'txt_special_char_ratio', 'txt_space_ratio',
                     'txt_garbled_word_count', 'txt_garbled_ratio',
                     'txt_has_transaction_id', 'txt_transaction_id_length',
                     'txt_has_amount', 'txt_amount_decimal_places',
                     'txt_has_balance', 'txt_has_date', 'txt_has_ref',
                     'txt_has_sender_name', 'txt_field_count',
                     'txt_line_length_var', 'txt_consecutive_caps_count']:
            features[key] = 0
        return features

    text = raw_text

    # Basic text statistics
    features['txt_total_chars'] = len(text)
    words = text.split()
    features['txt_total_words'] = len(words)
    lines = text.split('\n')
    features['txt_total_lines'] = len(lines)
    features['txt_avg_word_length'] = np.mean([len(w) for w in words]) if words else 0

    # Character composition
    features['txt_digit_ratio'] = sum(c.isdigit() for c in text) / len(text) if len(text) > 0 else 0
    features['txt_upper_ratio'] = sum(c.isupper() for c in text) / len(text) if len(text) > 0 else 0
    features['txt_special_char_ratio'] = sum(not c.isalnum() and not c.isspace() for c in text) / len(text) if len(text) > 0 else 0
    features['txt_space_ratio'] = sum(c.isspace() for c in text) / len(text) if len(text) > 0 else 0

    # OCR error detection
    garbled_words = [w for w in words if len(w) > 20 or
                     (len(w) > 8 and sum(c.isdigit() for c in w) / len(w) > 0.3 and
                      sum(c.isalpha() for c in w) / len(w) > 0.3)]
    features['txt_garbled_word_count'] = len(garbled_words)
    features['txt_garbled_ratio'] = len(garbled_words) / len(words) if words else 0

    # Transaction ID validation
    text_lower = text.lower()
    mfds_match = re.findall(r'mfds[a-z0-9]+', text_lower)
    any_id_match = re.findall(r'[a-z0-9]{15,}', text_lower)
    features['txt_has_transaction_id'] = 1 if (mfds_match or any_id_match) else 0
    if mfds_match:
        features['txt_transaction_id_length'] = len(mfds_match[0])
    elif any_id_match:
        features['txt_transaction_id_length'] = len(any_id_match[0])
    else:
        features['txt_transaction_id_length'] = 0

    # Amount format
    amount_patterns = re.findall(r'(?:NGN|₦|N)?\s?[\d,]+\.?\d*', text)
    features['txt_has_amount'] = 1 if amount_patterns else 0
    features['txt_amount_decimal_places'] = 0
    if amount_patterns:
        for amt in amount_patterns:
            if '.' in amt:
                features['txt_amount_decimal_places'] = len(amt.split('.')[-1])
                break

    # Field presence
    features['txt_has_balance'] = 1 if re.search(r'(?:bal|balance|avail)', text_lower) else 0
    features['txt_has_date'] = 1 if re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}', text) else 0
    features['txt_has_ref'] = 1 if re.search(r'(?:ref|reference|txn)', text_lower) else 0
    features['txt_has_sender_name'] = 1 if re.search(r'(?:from|sender|to)\s+[A-Z][a-z]+', text) else 0
    features['txt_field_count'] = (features['txt_has_transaction_id'] + features['txt_has_amount'] +
                                    features['txt_has_balance'] + features['txt_has_date'] +
                                    features['txt_has_ref'] + features['txt_has_sender_name'])

    # Line length variance
    line_lengths = [len(line.strip()) for line in lines if line.strip()]
    features['txt_line_length_var'] = np.var(line_lengths) if len(line_lengths) > 1 else 0

    # Consecutive capitals
    caps_runs = re.findall(r'[A-Z]{3,}', text)
    features['txt_consecutive_caps_count'] = len(caps_runs)

    return features
