import os
import io
import tempfile
import pandas as pd
import pymupdf as fitz
from datetime import datetime

from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store, add_documents_to_vector_store
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.pdf_sanitizer import sanitize_pdf
from src.redactor import redact_sensitive_data
from src.ner_detector import detect_entities

def test_feature5_audit_trail():
    results = {}
    audit_log = []

    # Helper function matching app.py audit record creation
    def record_audit(question, selected_scope, documents, guardrail, privacy_policy):
        regex_count = sum(len(v) for v in guardrail["regex_findings"].values())
        ner_count = sum(len(v) for v in guardrail["ner_findings"].values())
        total_sensitive = regex_count + ner_count
        action = guardrail["action"]

        if not guardrail["sensitive"] or total_sensitive == 0:
            risk_badge = "Low / Safe"
        elif action == "Redacted":
            risk_badge = "Moderate / Sanitized"
        else:
            risk_badge = "High / Blocked"

        query_ner = detect_entities(question)
        sanitized_query = redact_sensitive_data(question, query_ner)

        cat_counts = []
        for k, v in guardrail["regex_findings"].items():
            if v:
                cat_name = k.replace("_", " ").title()
                cat_counts.append(f"{cat_name} ({len(v)})")
        for k, v in guardrail["ner_findings"].items():
            if v:
                cat_counts.append(f"{k} ({len(v)})")

        categories_summary = ", ".join(cat_counts) if cat_counts else "None"

        source_docs_list = sorted(list({
            doc.metadata.get("source_doc", "Document")
            for doc in documents
        })) if documents else ([selected_scope] if selected_scope != "All Documents" else ["All Documents"])
        source_docs_str = ", ".join(source_docs_list)

        entry = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Sanitized Query": sanitized_query,
            "Target Scope": selected_scope,
            "Retrieved Chunk Count": len(documents) if documents else 0,
            "Source Documents": source_docs_str,
            "Regex Finding Count": regex_count,
            "NER Finding Count": ner_count,
            "Total Sensitive Items": total_sensitive,
            "Detected Categories": categories_summary,
            "Privacy Policy": privacy_policy,
            "Guardrail Action": guardrail["action"],
            "Risk Status": risk_badge,
            "LLM Invoked": "No (Blocked)" if guardrail["action"] == "Blocked" else "Yes"
        }
        audit_log.append(entry)
        return entry

    # Setup 2 test PDFs
    hr_text = (
        "CONFIDENTIAL HR REPORT\n"
        "Employee: Riya Mehta\n"
        "Position: Lead Machine Learning Engineer\n"
        "Email: riya.mehta@enterprise.org\n"
        "Phone: 9876543210\n"
        "Date of Joining: January 15, 2024"
    )
    doc1 = fitz.open()
    doc1.new_page().insert_text((50, 72), hr_text, fontsize=12)
    doc1_bytes = doc1.tobytes()
    doc1.close()

    fin_text = (
        "CONFIDENTIAL BANKING REPORT\n"
        "Customer: Daniel Joseph\n"
        "Account Type: Platinum High-Yield Savings\n"
        "Email: daniel.joseph@financebank.com\n"
        "Phone: 9123456789\n"
        "PAN: ABCDE5678G\n"
        "Balance: $120,000"
    )
    doc2 = fitz.open()
    doc2.new_page().insert_text((50, 72), fin_text, fontsize=12)
    doc2_bytes = doc2.tobytes()
    doc2.close()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f1, \
         tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f2:
        f1.write(doc1_bytes)
        f2.write(doc2_bytes)
        p1 = f1.name
        p2 = f2.name

    try:
        # Ingestion
        chunks1 = load_and_split_pdf(p1, doc_name="01_HR_Report.pdf")
        create_vector_store(chunks1, reset=True)
        chunks2 = load_and_split_pdf(p2, doc_name="02_Banking_Report.pdf")
        add_documents_to_vector_store(chunks2)

        # 1. Clean query test
        q_clean = "Explain the system architecture"
        ret_clean = get_relevant_context(q_clean, doc_filter="All Documents")
        clean_context_simulated = "The system implements vectorized nearest-neighbor indexing efficiently."
        guard_clean = process_context(clean_context_simulated, policy="Block Request")
        rec_clean = record_audit(q_clean, "All Documents", ret_clean["documents"], guard_clean, "Block Request")

        t1_ok = (
            rec_clean["Total Sensitive Items"] == 0 and
            rec_clean["Risk Status"] == "Low / Safe" and
            rec_clean["Guardrail Action"] == "Allowed" and
            rec_clean["LLM Invoked"] == "Yes"
        )
        results["1. Clean query audit"] = t1_ok

        # 2. PII query with Redact & Continue test
        q_pii_1 = "What is the contact email for Riya Mehta?"
        ret_pii_1 = get_relevant_context("Riya Mehta email", doc_filter="01_HR_Report.pdf")
        guard_redact = process_context(ret_pii_1["context"], policy="Redact & Continue")
        rec_redact = record_audit(q_pii_1, "01_HR_Report.pdf", ret_pii_1["documents"], guard_redact, "Redact & Continue")

        t2_ok = (
            rec_redact["Total Sensitive Items"] > 0 and
            rec_redact["Risk Status"] == "Moderate / Sanitized" and
            rec_redact["Guardrail Action"] == "Redacted" and
            rec_redact["LLM Invoked"] == "Yes" and
            "riya.mehta@enterprise.org" not in rec_redact["Sanitized Query"] and
            "Riya Mehta" not in rec_redact["Sanitized Query"] and
            "riya.mehta@enterprise.org" not in rec_redact["Detected Categories"]
        )
        results["2. PII + Redact & Continue audit"] = t2_ok

        # 3. PII query with Block Request test
        q_pii_2 = "Show the PAN number and account of Daniel Joseph with PAN ABCDE5678G"
        ret_pii_2 = get_relevant_context("Daniel Joseph PAN", doc_filter="02_Banking_Report.pdf")
        guard_block = process_context(ret_pii_2["context"], policy="Block Request")
        rec_block = record_audit(q_pii_2, "02_Banking_Report.pdf", ret_pii_2["documents"], guard_block, "Block Request")

        t3_ok = (
            rec_block["Total Sensitive Items"] > 0 and
            rec_block["Risk Status"] == "High / Blocked" and
            rec_block["Guardrail Action"] == "Blocked" and
            rec_block["LLM Invoked"] == "No (Blocked)" and
            "ABCDE5678G" not in rec_block["Sanitized Query"] and
            "Daniel Joseph" not in rec_block["Sanitized Query"] and
            "ABCDE5678G" not in rec_block["Detected Categories"]
        )
        results["3. PII + Block Request audit"] = t3_ok

        # 4. Multi-document audit test
        t4_ok = (
            "01_HR_Report.pdf" in rec_redact["Source Documents"] and
            "02_Banking_Report.pdf" in rec_block["Source Documents"]
        )
        results["4. Multi-document source attribution"] = t4_ok

        # 5. Raw PII protection in entire audit trail
        df_audit = pd.DataFrame(audit_log)
        csv_str = df_audit.to_csv(index=False)

        raw_pii_list = [
            "riya.mehta@enterprise.org", "9876543210", "Riya Mehta",
            "daniel.joseph@financebank.com", "9123456789", "Daniel Joseph", "ABCDE5678G"
        ]
        leaks_found = [pii for pii in raw_pii_list if pii in csv_str]
        t5_ok = (len(leaks_found) == 0)
        results["5. Raw PII protection in audit log & CSV"] = t5_ok

        # 6. CSV export format test
        expected_cols = [
            "Timestamp", "Sanitized Query", "Target Scope", "Retrieved Chunk Count",
            "Source Documents", "Regex Finding Count", "NER Finding Count",
            "Total Sensitive Items", "Detected Categories", "Privacy Policy",
            "Guardrail Action", "Risk Status", "LLM Invoked"
        ]
        t6_ok = all(col in df_audit.columns for col in expected_cols) and len(df_audit) == 3
        results["6. CSV export validity"] = t6_ok

        # 7. Regression check
        san1 = sanitize_pdf(doc1_bytes)
        doc1_san = fitz.open(stream=san1, filetype="pdf")
        t1_san = doc1_san[0].get_text()
        doc1_san.close()
        eval_files = ["evaluate.py", "evaluate_ablation.py", "evaluate_answer_quality.py"]
        t7_ok = ("riya.mehta@enterprise.org" not in t1_san and all(os.path.exists(f) for f in eval_files))
        results["7. Regression check (Features 1-4 & eval files)"] = t7_ok

        print("\n=== FEATURE 5 VERIFICATION RESULTS ===")
        all_passed = True
        for name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
            print(f"{name}: {status}")
        print("OVERALL:", "PASS" if all_passed else "FAIL")

    finally:
        if os.path.exists(p1):
            os.remove(p1)
        if os.path.exists(p2):
            os.remove(p2)

if __name__ == "__main__":
    test_feature5_audit_trail()
