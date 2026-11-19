from typing import Union
import pymupdf as fitz

from src.privacy_detector import detect_findings


def sanitize_pdf(pdf_input: Union[str, bytes]) -> bytes:
    """
    Sanitizes a PDF by detecting PII via Regex and NER, locating text on pages,
    and applying true permanent PDF redactions. The original PDF is left untouched.

    Args:
        pdf_input: File path (str) or raw bytes (bytes) of the PDF.

    Returns:
        bytes: Raw bytes of the sanitized PDF.
    """
    if isinstance(pdf_input, bytes):
        doc = fitz.open(stream=pdf_input, filetype="pdf")
    else:
        doc = fitz.open(pdf_input)

    try:
        for page in doc:
            page_text = page.get_text()
            if not page_text.strip():
                continue

            findings = detect_findings(page_text)
            terms_to_redact = {
                finding.matched_text
                for finding in findings
                if finding.classification == "sensitive"
                and finding.matched_text.strip()
            }

            # 3. Search and apply redaction annotations for each term
            # Sort by length descending to match composite phrases cleanly
            sorted_terms = sorted(terms_to_redact, key=len, reverse=True)

            for term in sorted_terms:
                rects = page.search_for(term)
                for rect in rects:
                    # Add redaction annotation with solid black fill
                    page.add_redact_annot(rect, fill=(0, 0, 0))

            # 4. Permanently apply redactions to excise underlying text & graphics
            page.apply_redactions()

        # Output sanitized PDF to bytes
        sanitized_bytes = doc.tobytes(deflate=True, garbage=3)
        return sanitized_bytes

    finally:
        doc.close()
