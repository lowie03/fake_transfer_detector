# =============================================================================
# EXPLANATION GENERATOR
# Drop-in replacement for _build_reasons() in both pipeline files.
# Produces plain, human-readable explanations for vendors/SMEs.
# =============================================================================
#
# USAGE:
#   from .explanations import build_screenshot_explanation, build_sms_explanation
#   Then call instead of the inline _build_reasons() methods.
#
# =============================================================================


def build_screenshot_explanation(tpl_feats, txt_feats, bank, prediction,
                                  compliance_score=None):
    """
    Build a plain-language explanation for a screenshot/receipt result.

    Designed for non-technical users (vendors, SMEs).
    Avoids technical terms like OCR, template, entropy, SHAP.

    Returns a list of up to 4 short sentences.
    """
    reasons = []

    # ── GENUINE path ─────────────────────────────────────────────────────────
    if prediction == "GENUINE":
        lines = []

        score = tpl_feats.get('tpl_field_completeness_pct', 0)
        if score >= 80:
            lines.append(
                f"All expected {bank} receipt fields were found."
            )
        elif score >= 50:
            lines.append(
                f"Most expected {bank} receipt fields were found."
            )

        if tpl_feats.get('tpl_branding_present', 0):
            lines.append(f"{bank} bank name was detected in the receipt.")

        if tpl_feats.get('tpl_status_correct', 0):
            lines.append("The transaction status wording is correct.")

        if not lines:
            lines.append(
                "The receipt structure matches what is expected for this bank."
            )

        return lines[:3]

    # ── FAKE path ─────────────────────────────────────────────────────────────

    # 1. Missing fields — most important, most understandable
    missing_n = tpl_feats.get('tpl_missing_fields_count', 0)
    total_n   = tpl_feats.get('tpl_expected_fields_total', 0)
    if missing_n > 0 and total_n > 0:
        reasons.append(
            f"This receipt is missing {missing_n} out of {total_n} "
            f"fields that a real {bank} receipt must have."
        )

    # 2. Required keywords not found
    kw_ratio = tpl_feats.get('tpl_required_keywords_ratio', 1.0)
    if kw_ratio < 0.5:
        reasons.append(
            f"Key words and labels expected on a {bank} receipt "
            f"were not found in this document."
        )

    # 3. Wrong status wording
    if tpl_feats.get('tpl_status_wrong', 0):
        reasons.append(
            f"The transaction status on this receipt uses wording "
            f"that {bank} does not use on real receipts."
        )

    # 4. Missing disclaimer / footer
    if (tpl_feats.get('tpl_disclaimer_expected', 0)
            and not tpl_feats.get('tpl_disclaimer_present', 0)):
        reasons.append(
            f"The security disclaimer that appears at the bottom of "
            f"every real {bank} receipt is missing."
        )

    # 5. Amount in words missing (GTBank specific)
    if (tpl_feats.get('tpl_amount_in_words_expected', 0)
            and not tpl_feats.get('tpl_amount_in_words_present', 0)):
        reasons.append(
            f"{bank} always writes the amount in words on real receipts "
            f"(e.g. 'Five Thousand Naira'). This receipt does not have that."
        )

    # 6. Bank name not detected
    if not tpl_feats.get('tpl_branding_present', 0) and bank != 'unknown':
        reasons.append(
            f"The {bank} bank name or logo text was not detected "
            f"anywhere on this receipt."
        )

    # 7. Poor text quality — OCR couldn't read it properly
    garbled = txt_feats.get('txt_garbled_ratio', 0)
    field_n  = txt_feats.get('txt_field_count', 6)
    if garbled > 0.15:
        reasons.append(
            "The text on this receipt is unclear or corrupted. "
            "This can happen if the image was edited or heavily compressed."
        )
    elif field_n < 2:
        reasons.append(
            "Very little readable text was found in this receipt. "
            "A genuine receipt should clearly show the amount, date, "
            "and reference number."
        )

    # 8. Low overall compliance — catch-all
    score = tpl_feats.get('tpl_template_score', 0)
    if not reasons and score < 0.4:
        reasons.append(
            f"This receipt does not follow the standard layout "
            f"of a genuine {bank} receipt."
        )

    # 9. Absolute fallback
    if not reasons:
        reasons.append(
            "The receipt failed several automatic checks. "
            "Please verify this payment directly with your bank."
        )

    return reasons[:4]


def build_sms_explanation(tpl_feats, meta_feats, bank, prediction):
    """
    Build a plain-language explanation for an SMS alert result.

    Designed for non-technical users (vendors, SMEs).

    Returns a list of up to 4 short sentences.
    """
    reasons = []

    # ── GENUINE path ─────────────────────────────────────────────────────────
    if prediction == "GENUINE":
        lines = []

        if tpl_feats.get('sms_tpl_keywords_ratio', 0) >= 0.7:
            lines.append(
                f"The SMS contains the expected fields for a {bank} alert."
            )
        if tpl_feats.get('sms_tpl_amount_format_valid', 0):
            lines.append("The amount format matches the bank standard.")
        if tpl_feats.get('sms_tpl_desc_keyword_found', 0):
            lines.append("The transaction description looks genuine.")
        if not lines:
            lines.append(
                "This SMS matches the structure of a real bank alert."
            )
        return lines[:3]

    # ── FAKE path ─────────────────────────────────────────────────────────────

    # 1. Missing required fields
    missing_n = (tpl_feats.get('sms_tpl_keywords_total', 0)
                 - tpl_feats.get('sms_tpl_keywords_found', 0))
    if missing_n > 0:
        reasons.append(
            f"This SMS is missing {missing_n} field(s) that every real "
            f"{bank} transaction alert must include."
        )

    # 2. Amount format wrong
    if not tpl_feats.get('sms_tpl_amount_format_valid', 1):
        reasons.append(
            f"The way the amount is written does not match how "
            f"{bank} formats it on real alerts."
        )

    # 3. Suspicious phrases
    if meta_feats.get('meta_has_suspicious_phrase', 0):
        reasons.append(
            "This SMS contains phrases like 'click here' or 'verify account' "
            "that real bank alerts never use."
        )

    # 4. Suspicious sender
    if meta_feats.get('meta_has_suspicious_name', 0):
        reasons.append(
            "The sender name looks suspicious and does not match a real bank."
        )

    # 5. Amount almost equals balance (common in fake screenshots)
    if (meta_feats.get('meta_amt_bal_ratio', 0) > 0.95
            and meta_feats.get('meta_amount', 0) > 0):
        reasons.append(
            "The transfer amount is almost the same as the account balance, "
            "which is unusual for a genuine credit alert."
        )

    # 6. Wrong branding for GTBank
    if (meta_feats.get('meta_has_gtbank', 0)
            and not meta_feats.get('meta_has_gtworld', 0)
            and bank == 'GTBank'):
        reasons.append(
            "Real GTBank alerts come from 'GTWorld', not 'GTBANK'. "
            "This SMS uses the wrong sender name."
        )

    # 7. Too few fields
    fields_present = meta_feats.get('meta_fields_present', 10)
    if fields_present < 3:
        reasons.append(
            f"This SMS only contains {fields_present} of the fields "
            f"expected in a real bank alert (account, amount, balance, date)."
        )

    # 8. Template score catch-all
    if not reasons and tpl_feats.get('sms_tpl_template_score', 1) < 0.4:
        reasons.append(
            f"This SMS does not follow the standard format of a "
            f"genuine {bank} transaction alert."
        )

    # 9. Absolute fallback
    if not reasons:
        reasons.append(
            "This SMS failed several automatic checks. "
            "Please verify this transaction directly with your bank."
        )

    return reasons[:4]


def format_explanation_for_display(reasons, prediction, bank):
    """
    Format the reasons list into a single display string.
    Joins reasons with ' · ' separator for compact UI display,
    or returns them as a list for multi-line display.

    Args:
        reasons:    list of reason strings
        prediction: 'FAKE' or 'GENUINE'
        bank:       bank name string

    Returns:
        dict with 'summary' (one sentence) and 'details' (list)
    """
    if prediction == "GENUINE":
        summary = f"This receipt appears to be a genuine {bank} transaction."
    else:
        summary = (
            "This receipt has been flagged as potentially fraudulent. "
            "Do not confirm payment until you have verified it with your bank."
        )

    return {
        'summary': summary,
        'details': reasons,
        'display': " · ".join(reasons),
    }