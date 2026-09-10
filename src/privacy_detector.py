import re


# =========================================
# Regular Expression Patterns
# =========================================

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

PHONE_PATTERN = r"\b\d{10}\b"
PAN_PATTERN = r"\b[A-Z]{5,6}[0-9]{4}[A-Z]\b"

AADHAAR_PATTERN = r"\b\d{4}\s\d{4}\s\d{4}\b"

# Bank account numbers: 10 to 18 consecutive digits
BANK_ACCOUNT_PATTERN = r"\b\d{10,18}\b"

# IFSC-style code: 4 letters + 0 + 6 alphanumeric characters
IFSC_PATTERN = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"

# Credit-card-like number: 16 digits
CREDIT_CARD_PATTERN = r"\b(?:\d{4}[- ]?){3}\d{4}\b"

# Government ID formats used in the synthetic dataset
GOVERNMENT_ID_PATTERN = r"\b[A-Z]{2,10}-ID-[A-Z]{2,5}-?\d{4,8}\b"


# =========================================
# Detection Functions
# =========================================

def detect_emails(text: str):
    return re.findall(EMAIL_PATTERN, text)


def detect_phone_numbers(text: str):
    return re.findall(PHONE_PATTERN, text)


def detect_pan_numbers(text: str):
    return re.findall(PAN_PATTERN, text)


def detect_aadhaar_numbers(text: str):
    return re.findall(AADHAAR_PATTERN, text)


def detect_bank_accounts(text: str):
    return re.findall(BANK_ACCOUNT_PATTERN, text)


def detect_ifsc_codes(text: str):
    return re.findall(IFSC_PATTERN, text)


def detect_credit_cards(text: str):
    return re.findall(CREDIT_CARD_PATTERN, text)


def detect_government_ids(text: str):
    return re.findall(GOVERNMENT_ID_PATTERN, text)


# =========================================
# Master Scanner
# =========================================

def scan_sensitive_data(text: str):
    """
    Scan text for sensitive information.

    Returns:
        dict: Detected sensitive data.
    """

    try:
        return {
            "emails": detect_emails(text),
            "phone_numbers": detect_phone_numbers(text),
            "pan_numbers": detect_pan_numbers(text),
            "aadhaar_numbers": detect_aadhaar_numbers(text),
            "bank_accounts": detect_bank_accounts(text),
            "ifsc_codes": detect_ifsc_codes(text),
            "credit_cards": detect_credit_cards(text),
            "government_ids": detect_government_ids(text)
        }

    except Exception as e:
        raise Exception(f"Privacy Detection Error: {e}")