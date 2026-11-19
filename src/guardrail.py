"""Privacy policy decisions for user queries and retrieved document context."""

from dataclasses import replace

from src.privacy_detector import DetectionFinding, detect_findings
from src.redactor import redact_sensitive_data


_REGEX_CATEGORIES = {
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


def _classify(text: str, location: str) -> list[DetectionFinding]:
    return [
        replace(finding, location=location)
        for finding in detect_findings(text)
    ]


def _legacy_findings(findings: list[DetectionFinding], source: str) -> dict[str, list[str]]:
    result = (
        {category: [] for category in _REGEX_CATEGORIES.values()}
        if source == "Regex"
        else {}
    )
    for finding in findings:
        if finding.source == source and finding.classification == "sensitive":
            category = (
                _REGEX_CATEGORIES[finding.category]
                if source == "Regex"
                else finding.category
            )
            result.setdefault(category, []).append(finding.matched_text)
    return result


def process_context(
    context: str,
    policy: str = "Redact & Continue",
    query: str = "",
) -> dict[str, object]:
    """Apply the selected policy to confirmed findings in both prompt inputs."""
    context_findings = _classify(context, "context")
    query_findings = _classify(query, "query") if query else []
    findings = context_findings + query_findings
    sensitive_findings = [
        finding for finding in findings if finding.classification == "sensitive"
    ]
    uncertain_findings = [
        finding for finding in findings if finding.classification == "uncertain"
    ]
    sensitive = bool(sensitive_findings)
    block_requested = policy in {"Block Request", "block"}
    blocked = sensitive and block_requested

    safe_context = (
        None
        if blocked
        else redact_sensitive_data(context, findings=context_findings)
    )
    safe_query = (
        None
        if blocked
        else redact_sensitive_data(query, findings=query_findings)
    )

    final_findings = []
    for finding in findings:
        redaction_status = (
            "redacted"
            if finding.classification == "sensitive" and not blocked
            else "blocked"
            if finding.classification == "sensitive"
            else "not_required"
        )
        final_findings.append(replace(finding, redaction_status=redaction_status))

    action = "Blocked" if blocked else "Redacted" if sensitive else "Allowed"
    categories = sorted({finding.category for finding in sensitive_findings})
    rationale = (
        f"Confirmed {', '.join(categories)} finding(s) "
        + ("triggered the blocking policy." if blocked else "were redacted before generation.")
        if sensitive
        else "No high-confidence personal identifiers were detected."
    )
    if uncertain_findings:
        uncertain_categories = sorted({finding.category for finding in uncertain_findings})
        rationale += (
            " Uncertain "
            + ", ".join(uncertain_categories)
            + " candidates were not treated as confirmed PII or used to block the request."
        )

    return {
        "safe_context": safe_context,
        "safe_query": safe_query,
        "regex_findings": _legacy_findings(findings, "Regex"),
        "ner_findings": _legacy_findings(findings, "NER"),
        "findings": final_findings,
        "sensitive": sensitive,
        "action": action,
        "blocked": blocked,
        "rationale": rationale,
    }
