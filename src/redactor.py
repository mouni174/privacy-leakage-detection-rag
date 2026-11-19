"""Span-based redaction for confirmed identifiers and contextual entities."""

from src.privacy_detector import (
    AADHAAR_PATTERN,
    BANK_ACCOUNT_PATTERN,
    CREDIT_CARD_PATTERN,
    EMAIL_PATTERN,
    GOVERNMENT_ID_PATTERN,
    IFSC_PATTERN,
    PAN_PATTERN,
    PHONE_PATTERN,
    DetectionFinding,
    detect_findings,
)


_REPLACEMENTS = {
    "EMAIL": "[EMAIL REDACTED]",
    "PHONE": "[PHONE REDACTED]",
    "PAN": "[PAN REDACTED]",
    "AADHAAR": "[AADHAAR REDACTED]",
    "BANK_ACCOUNT": "[BANK ACCOUNT REDACTED]",
    "IFSC": "[IFSC REDACTED]",
    "CREDIT_CARD": "[CARD REDACTED]",
    "GOVERNMENT_ID": "[ID REDACTED]",
    "INTERNAL_ID": "[INTERNAL ID REDACTED]",
    "HEALTH_INFO": "[HEALTH INFORMATION REDACTED]",
    "PERSON": "[PERSON REDACTED]",
    "ORG": "[ORG REDACTED]",
    "GPE": "[LOCATION REDACTED]",
    "LOC": "[LOCATION REDACTED]",
    "DATE": "[DATE REDACTED]",
    "MONEY": "[AMOUNT REDACTED]",
}

NER_REDACTION_LABELS = {
    category: replacement
    for category, replacement in _REPLACEMENTS.items()
    if category in {"PERSON", "GPE", "LOC", "DATE", "MONEY", "ORG"}
}


def redact_sensitive_data(
    text: str,
    ner_findings=None,
    *,
    findings: list[DetectionFinding] | None = None,
    include_uncertain: bool = False,
) -> str:
    """Redact selected findings by their original spans without global replace."""
    del ner_findings
    detected = findings if findings is not None else detect_findings(text)
    selected = [
        finding
        for finding in detected
        if finding.classification == "sensitive"
        or (
            include_uncertain
            and finding.source == "NER"
            and finding.category == "PERSON"
            and finding.classification == "uncertain"
        )
    ]

    redacted = text
    for finding in sorted(selected, key=lambda item: item.start, reverse=True):
        replacement = _REPLACEMENTS.get(finding.category)
        if replacement is None:
            continue
        redacted = redacted[: finding.start] + replacement + redacted[finding.end :]
    return redacted
