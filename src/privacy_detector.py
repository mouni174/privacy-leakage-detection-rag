import re

# ==============================
# Regular Expression Patterns
# ==============================

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

PHONE_PATTERN = r"\b\d{10}\b"

PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

AADHAAR_PATTERN = r"\b\d{4}\s\d{4}\s\d{4}\b"


# ==============================
# Detection Functions
# ==============================

def detect_emails(text: str):
    return re.findall(EMAIL_PATTERN, text)


def detect_phone_numbers(text: str):
    return re.findall(PHONE_PATTERN, text)


def detect_pan_numbers(text: str):
    return re.findall(PAN_PATTERN, text)


def detect_aadhaar_numbers(text: str):
    return re.findall(AADHAAR_PATTERN, text)


# ==============================
# Master Scanner
# ==============================

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
            "aadhaar_numbers": detect_aadhaar_numbers(text)
        }

    except Exception as e:
        raise Exception(f"Privacy Detection Error: {e}")