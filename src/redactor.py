import re


# =========================================
# Regex Patterns
# =========================================

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

PHONE_PATTERN = r"\b\d{10}\b"
PAN_PATTERN = r"\b[A-Z]{5,6}[0-9]{4}[A-Z]\b"

AADHAAR_PATTERN = r"\b\d{4}\s\d{4}\s\d{4}\b"

BANK_ACCOUNT_PATTERN = r"\b\d{10,18}\b"

IFSC_PATTERN = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"

CREDIT_CARD_PATTERN = r"\b(?:\d{4}[- ]?){3}\d{4}\b"

GOVERNMENT_ID_PATTERN = r"\b[A-Z]{2,10}-ID-(?:[A-Z]{2,5}-)?\d{4,8}\b"


# =========================================
# NER Entities to Redact
# =========================================

NER_REDACTION_LABELS = {
    "PERSON": "[PERSON REDACTED]",
    "MONEY": "[MONEY REDACTED]",
    "ORG": "[ORG REDACTED]",
    "GPE": "[LOCATION REDACTED]",
    "LOC": "[LOCATION REDACTED]"
}


# =========================================
# Redaction
# =========================================

def redact_sensitive_data(text: str, ner_findings=None):
    """
    Redacts sensitive information using Regex and NER.
    """

    try:

        # -------------------------------------
        # 1. Regex-based redaction
        # -------------------------------------

        text = re.sub(
            EMAIL_PATTERN,
            "[EMAIL REDACTED]",
            text
        )

        text = re.sub(
            PHONE_PATTERN,
            "[PHONE REDACTED]",
            text
        )

        text = re.sub(
            PAN_PATTERN,
            "[PAN REDACTED]",
            text
        )

        text = re.sub(
            AADHAAR_PATTERN,
            "[AADHAAR REDACTED]",
            text
        )

        text = re.sub(
            IFSC_PATTERN,
            "[IFSC REDACTED]",
            text
        )

        text = re.sub(
            CREDIT_CARD_PATTERN,
            "[CARD REDACTED]",
            text
        )

        text = re.sub(
            GOVERNMENT_ID_PATTERN,
            "[ID REDACTED]",
            text
        )

        # Bank account numbers are processed after
        # phone numbers so phone numbers are not
        # replaced as bank accounts.
        text = re.sub(
            BANK_ACCOUNT_PATTERN,
            "[BANK_ACCOUNT REDACTED]",
            text
        )


        # -------------------------------------
        # 2. NER-based redaction
        # -------------------------------------

        if ner_findings:

            for label, entities in ner_findings.items():

                if label not in NER_REDACTION_LABELS:
                    continue

                replacement = NER_REDACTION_LABELS[label]

                for entity in entities:

                    entity = entity.strip()

                    if not entity:
                        continue

                    if entity in text:

                        text = text.replace(
                            entity,
                            replacement
                        )

        return text

    except Exception as e:

        raise Exception(
            f"Redaction Error: {e}"
        )