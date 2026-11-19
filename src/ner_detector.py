"""spaCy entity extraction with contextual PII classification."""

import re

import spacy

from src.privacy_detector import DetectionFinding


nlp = spacy.load("en_core_web_sm")

_SUPPORTED_LABELS = {"PERSON", "ORG", "GPE", "LOC", "DATE", "MONEY"}
_TECHNICAL_TERMS = {
    "java",
    "python",
    "sql",
    "react",
    "html",
    "css",
    "javascript",
    "machine learning",
    "artificial intelligence",
    "data structures",
    "algorithms",
    "chromadb",
    "langchain",
    "gemini",
    "tensorflow",
    "mysql",
    "github",
}
_PERSON_CUES = re.compile(
    r"\b(my name is|name\s*:|employee name\s*:|patient name\s*:|student name\s*:|"
    r"i am|i['’]m|candidate|applicant|resume of|cv of|contact person|account holder)"
    r"\s*[:,-]?\s*(?:mr|mrs|ms|miss|dr)?\s*$",
    re.IGNORECASE,
)
_LOCATION_CUES = re.compile(
    r"\b(home address|my address|reside at|residing at|i live at|i live in)"
    r"\s*(?:is|in|at)?\s*[:,-]?\s*$",
    re.IGNORECASE,
)
_BIRTH_DATE_CUES = re.compile(
    r"\b(date of birth|born on|birth date|dob)\s*(?:is|:)?\s*$",
    re.IGNORECASE,
)
_FINANCIAL_CUES = re.compile(
    r"\b(my salary|my income|salary is|income is|bank balance|account balance|"
    r"net worth|my compensation)\s*(?:is|:)?\s*[$€£₹]?\s*$",
    re.IGNORECASE,
)


def detect_entity_findings(text: str) -> list[DetectionFinding]:
    """Return entity spans with contextual classification, not label-only PII."""
    doc = nlp(text)
    findings: list[DetectionFinding] = []

    for entity in doc.ents:
        if entity.label_ not in _SUPPORTED_LABELS:
            continue

        value = entity.text.strip()
        if not value:
            continue

        sentence_start = max(
            text.rfind(separator, 0, entity.start_char)
            for separator in ("\n", ".", "!", "?", ";")
        )
        prefix = text[sentence_start + 1 : entity.start_char]
        normalized = " ".join(value.casefold().split())
        category = entity.label_
        if _PERSON_CUES.search(prefix):
            category = "PERSON"
            classification = "sensitive"
            confidence = 0.92
            rationale = "A personal-name entity appears in an explicit identity context."
        elif normalized in _TECHNICAL_TERMS:
            classification = "non_sensitive"
            confidence = 0.99
            rationale = (
                "The exact entity matches an explicit technical term; this does not "
                "override structured identifier matches."
            )
        elif entity.label_ in {"GPE", "LOC"} and _LOCATION_CUES.search(prefix):
            classification = "sensitive"
            confidence = 0.86
            rationale = "A location appears in explicit home or residence context."
        elif entity.label_ == "DATE" and _BIRTH_DATE_CUES.search(prefix):
            classification = "sensitive"
            confidence = 0.95
            rationale = "A date appears in an explicit date-of-birth context."
        elif entity.label_ == "MONEY" and _FINANCIAL_CUES.search(prefix):
            classification = "sensitive"
            confidence = 0.84
            rationale = "An amount appears in personal income or account context."
        elif entity.label_ == "PERSON":
            classification = "uncertain"
            confidence = 0.55
            rationale = (
                "spaCy identified a person-like span, but the surrounding text does "
                "not establish that it identifies the user."
            )
        else:
            classification = "non_sensitive"
            confidence = 0.3
            rationale = (
                f"A {entity.label_} mention is not a personal identifier without "
                "personal context."
            )

        findings.append(
            DetectionFinding(
                category=category,
                source="NER",
                start=entity.start_char,
                end=entity.end_char,
                matched_text=value,
                confidence=confidence,
                rationale=rationale,
                classification=classification,
            )
        )

    return findings


def detect_entities(text: str) -> dict[str, list[str]]:
    """Preserve the legacy entity-grouping API for existing research scripts."""
    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],
        "LOC": [],
        "DATE": [],
        "MONEY": [],
    }
    for finding in detect_entity_findings(text):
        if finding.matched_text not in entities[finding.category]:
            entities[finding.category].append(finding.matched_text)
    return entities
