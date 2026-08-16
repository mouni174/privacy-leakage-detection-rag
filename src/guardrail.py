from src.privacy_detector import scan_sensitive_data
from src.redactor import redact_sensitive_data
from src.ner_detector import detect_entities

def process_context(context):

    regex_findings = scan_sensitive_data(context)

    ner_findings = detect_entities(context)

    has_regex = any(
        len(v) > 0
        for v in regex_findings.values()
    )

    has_ner = any(
        len(v) > 0
        for v in ner_findings.values()
    )

    sensitive = has_regex or has_ner

    if sensitive:

        safe_context = redact_sensitive_data(
    context,
    ner_findings
)

        action = "Redacted"

    else:

        safe_context = context

        action = "Allowed"

    return {

        "safe_context": safe_context,

        "regex_findings": regex_findings,

        "ner_findings": ner_findings,

        "sensitive": sensitive,

        "action": action

    }