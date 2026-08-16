import re


# =========================================
# Regex Patterns
# =========================================

EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

PHONE_PATTERN = r"\b\d{10}\b"

PAN_PATTERN = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

AADHAAR_PATTERN = r"\b\d{4}\s\d{4}\s\d{4}\b"


# =========================================
# NER Entities We Consider Sensitive
# =========================================

NER_REDACTION_LABELS = {
    "PERSON": "[PERSON REDACTED]",
    "MONEY": "[MONEY REDACTED]"
}


# =========================================
# Redaction
# =========================================

def redact_sensitive_data(text: str, ner_findings=None):
    """
    Redacts structured PII using Regex and selected
    sensitive entities detected using NER.
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

                    # Avoid replacing text that has already
                    # been converted into a redaction marker.
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