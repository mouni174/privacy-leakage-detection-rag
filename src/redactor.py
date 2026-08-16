import re

# ==============================
# Regular Expression Patterns
# ==============================

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

PHONE_PATTERN = r"\b\d{10}\b"

PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

AADHAAR_PATTERN = r"\b\d{4}\s\d{4}\s\d{4}\b"


def redact_sensitive_data(text: str):
    """
    Redacts sensitive information from the retrieved context.

    Args:
        text (str): Retrieved document text.

    Returns:
        str: Sanitized text with sensitive information masked.
    """

    try:
        text = re.sub(EMAIL_PATTERN, "[EMAIL REDACTED]", text)

        text = re.sub(PHONE_PATTERN, "[PHONE REDACTED]", text)

        text = re.sub(PAN_PATTERN, "[PAN REDACTED]", text)

        text = re.sub(AADHAAR_PATTERN, "[AADHAAR REDACTED]", text)

        return text

    except Exception as e:
        raise Exception(f"Redaction Error: {e}")
    