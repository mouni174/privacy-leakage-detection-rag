"""Context-aware detection for structured personal identifiers."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class DetectionFinding:
    category: str
    source: str
    start: int
    end: int
    matched_text: str
    confidence: float
    rationale: str
    classification: str
    redaction_status: str = "not_processed"
    location: str = "context"

    def safe_record(self) -> dict[str, object]:
        """Return finding metadata without its potentially sensitive text."""
        return {
            "category": self.category,
            "source": self.source,
            "span": (self.start, self.end),
            "confidence": self.confidence,
            "rationale": self.rationale,
            "classification": self.classification,
            "redaction_status": self.redaction_status,
            "location": self.location,
        }


EMAIL_PATTERN = (
    r"(?<![\w.+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
)
PHONE_PATTERN = r"(?<!\d)\+?(?:\d[\s().-]*){5,13}\d(?!\d)"
PAN_PATTERN = r"\b[A-Z]{3}[PCHFATBLJG][A-Z][0-9]{4}[A-Z]\b"
AADHAAR_PATTERN = r"(?<!\d)[2-9]\d{3}(?:[ -]?\d{4}){2}(?!\d)"
BANK_ACCOUNT_PATTERN = r"(?<!\d)(?:\d[ -]?){10,17}\d(?!\d)"
IFSC_PATTERN = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
CREDIT_CARD_PATTERN = r"(?<!\d)\d(?:[ -]?\d){11,17}\d(?!\d)"
GOVERNMENT_ID_PATTERN = (
    r"\b[A-Z]{2,10}-ID-(?:[A-Z]{2,5}-)?\d{4,8}\b"
)
INTERNAL_ID_PATTERN = (
    r"\b(?:EMP|EID|STAFF|PATIENT|PAT|STUDENT|STU)[-_]"
    r"[A-Z0-9]{4,12}\b"
)
HEALTH_INFO_PATTERN = (
    r"\b(?:diagnosis|medical condition|medication|treatment|allergy)"
    r"\s*(?:is|:)\s*([A-Za-z0-9][^.;\n]{1,80})"
)

_PATTERNS = (
    ("EMAIL", re.compile(EMAIL_PATTERN, re.IGNORECASE)),
    ("PAN", re.compile(PAN_PATTERN, re.IGNORECASE)),
    ("GOVERNMENT_ID", re.compile(GOVERNMENT_ID_PATTERN, re.IGNORECASE)),
    ("INTERNAL_ID", re.compile(INTERNAL_ID_PATTERN, re.IGNORECASE)),
    ("HEALTH_INFO", re.compile(HEALTH_INFO_PATTERN, re.IGNORECASE)),
    ("CREDIT_CARD", re.compile(CREDIT_CARD_PATTERN)),
    ("AADHAAR", re.compile(AADHAAR_PATTERN)),
    ("BANK_ACCOUNT", re.compile(BANK_ACCOUNT_PATTERN)),
    ("PHONE", re.compile(PHONE_PATTERN)),
    ("IFSC", re.compile(IFSC_PATTERN, re.IGNORECASE)),
)

_CONTEXT = {
    "PHONE": re.compile(
        r"\b(phone|mobile|telephone|contact number|call me|text me|whatsapp)\b",
        re.IGNORECASE,
    ),
    "AADHAAR": re.compile(r"\b(aadhaar|aadhar|uidai|uid number)\b", re.IGNORECASE),
    "BANK_ACCOUNT": re.compile(
        r"\b(bank account|account number|account no\.?|acct\.?|a/c|beneficiary account)\b",
        re.IGNORECASE,
    ),
    "IFSC": re.compile(r"\b(ifsc|bank details)\b", re.IGNORECASE),
}

_LEGACY_KEYS = {
    "EMAIL": "emails",
    "PHONE": "phone_numbers",
    "PAN": "pan_numbers",
    "AADHAAR": "aadhaar_numbers",
    "BANK_ACCOUNT": "bank_accounts",
    "IFSC": "ifsc_codes",
    "CREDIT_CARD": "credit_cards",
    "GOVERNMENT_ID": "government_ids",
    "INTERNAL_ID": "internal_ids",
    "HEALTH_INFO": "health_information",
}


def _sentence_context(text: str, start: int, end: int) -> str:
    left = max(
        text.rfind(separator, 0, start)
        for separator in ("\n", ".", "!", "?", ";")
    )
    right_candidates = [
        position
        for separator in ("\n", ".", "!", "?", ";")
        if (position := text.find(separator, end)) >= 0
    ]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 : right]


def _luhn_valid(value: str) -> bool:
    digits = [int(character) for character in value if character.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def detect_regex_findings(text: str) -> list[DetectionFinding]:
    """Find structured identifiers and classify ambiguous numeric candidates."""
    candidates: list[DetectionFinding] = []
    for category, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            if category == "HEALTH_INFO":
                candidate = match.group(1).rstrip(" ,")
                start = match.start(1)
                end = start + len(candidate)
            else:
                candidate = match.group(0)
                start = match.start()
                end = match.end()
            if not candidate:
                continue
            surrounding = _sentence_context(text, start, end)
            context_pattern = _CONTEXT.get(category)
            has_context = bool(context_pattern and context_pattern.search(surrounding))

            if category == "HEALTH_INFO":
                classification = "sensitive"
                confidence = 0.94
                rationale = "The span follows an explicit health-information label."
            elif category == "CREDIT_CARD" and not _luhn_valid(candidate):
                continue
            elif category == "IFSC" and not has_context:
                classification = "non_sensitive"
                confidence = 0.3
                rationale = "An IFSC identifies a bank branch, not a person."
            elif category == "PHONE" and not has_context and not candidate.lstrip().startswith("+"):
                classification = "uncertain"
                confidence = 0.55
                rationale = (
                    "The value has a phone-like format but lacks confirming "
                    "telephone context."
                )
            elif category in {"AADHAAR", "BANK_ACCOUNT"} and not has_context:
                classification = "uncertain"
                confidence = 0.55
                rationale = (
                    "The value has an identifier-like format but lacks confirming "
                    "personal or financial context."
                )
            else:
                classification = "sensitive"
                confidence = 0.99 if category in {
                    "EMAIL",
                    "PAN",
                    "CREDIT_CARD",
                    "GOVERNMENT_ID",
                    "INTERNAL_ID",
                } else 0.94
                rationale = (
                    "The value matches a validated identifier pattern"
                    + (" and its surrounding context confirms its use." if has_context else ".")
                )

            candidates.append(
                DetectionFinding(
                    category=category,
                    source="Regex",
                    start=start,
                    end=end,
                    matched_text=candidate,
                    confidence=confidence,
                    rationale=rationale,
                    classification=classification,
                )
            )

    candidates.sort(key=lambda finding: (finding.start, -(finding.end - finding.start)))
    selected: list[DetectionFinding] = []
    for finding in candidates:
        if selected and finding.start < selected[-1].end:
            continue
        selected.append(finding)
    return selected


def detect_findings(text: str) -> list[DetectionFinding]:
    """Combine structured detection and contextual NER classification."""
    regex_findings = detect_regex_findings(text)
    from src.ner_detector import detect_entity_findings

    ner_findings = detect_entity_findings(text)
    regex_spans = [(finding.start, finding.end) for finding in regex_findings]
    ner_findings = [
        finding
        for finding in ner_findings
        if not any(
            finding.start < end and start < finding.end
            for start, end in regex_spans
        )
    ]
    return sorted(
        regex_findings + ner_findings,
        key=lambda finding: (finding.start, finding.end, finding.source),
    )


def scan_sensitive_data(text: str) -> dict[str, list[str]]:
    """Retain the legacy structured-scanner shape for research scripts."""
    findings = detect_regex_findings(text)
    result = {key: [] for key in _LEGACY_KEYS.values()}
    for finding in findings:
        if finding.classification == "sensitive":
            result[_LEGACY_KEYS[finding.category]].append(finding.matched_text)
    return result


def detect_emails(text: str) -> list[str]:
    return scan_sensitive_data(text)["emails"]


def detect_phone_numbers(text: str) -> list[str]:
    return scan_sensitive_data(text)["phone_numbers"]


def detect_pan_numbers(text: str) -> list[str]:
    return scan_sensitive_data(text)["pan_numbers"]


def detect_aadhaar_numbers(text: str) -> list[str]:
    return scan_sensitive_data(text)["aadhaar_numbers"]


def detect_bank_accounts(text: str) -> list[str]:
    return scan_sensitive_data(text)["bank_accounts"]


def detect_ifsc_codes(text: str) -> list[str]:
    return scan_sensitive_data(text)["ifsc_codes"]


def detect_credit_cards(text: str) -> list[str]:
    return scan_sensitive_data(text)["credit_cards"]


def detect_government_ids(text: str) -> list[str]:
    return scan_sensitive_data(text)["government_ids"]
