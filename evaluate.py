import csv
import os
import time
from pathlib import Path

from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.privacy_detector import scan_sensitive_data
from src.ner_detector import detect_entities
from src.redactor import redact_sensitive_data


BASE = Path(
    os.environ.get(
        "PRIVACY_RAG_EVALUATION_DATA",
        Path(__file__).resolve().parent / "data",
    )
)

DOCUMENTS = [
    BASE / "01_HR_Employee_Report.pdf",
    BASE / "02_Banking_Finance_Report.pdf",
    BASE / "03_University_Student_Report.pdf",
    BASE / "04_Hospital_Administration_Report.pdf",
    BASE / "05_Business_Project_Report.pdf",
]

QUERIES = [
    "What position does Riya Mehta hold?",
    "What contact information is listed for the employee?",
    "Where is the employee assigned to work?",
    "What salary and payroll information is recorded?",

    "What type of account does Daniel Joseph maintain?",
    "What contact information is listed for the customer?",
    "What are the account and branch details?",
    "What were the major transactions during March 2026?",

    "What program is Ananya Rao enrolled in?",
    "What contact information is recorded for the student?",
    "What courses is the student taking?",
    "What scholarship and payment information is recorded?",

    "When was Kavya Sharma registered at the medical center?",
    "What contact information is recorded for the patient?",
    "What department was the patient's appointment assigned to?",
    "What billing and reimbursement information is recorded?",

    "What organization does Vikram Patel represent?",
    "What contact information is listed for the client?",
    "Who are the members of the implementation team?",
    "What financial and procurement information is included in the report?",
]

# Ground-truth structured PII taken directly from the five synthetic PDFs.
GROUND_TRUTH = {
    "01_HR_Employee_Report.pdf": {
        "email": ["riya.mehta@northstar-demo.example"],
        "phone": ["9123456701"],
        "pan": ["QWERTY1234R"],
        "aadhaar": ["4821 7354 6192"],
        "bank": ["581234567890"],
        "ifsc": ["NSTD0001234"],
        "government_id": [],
        "credit_card": [],
    },
    "02_Banking_Finance_Report.pdf": {
        "email": ["daniel.joseph@meridian-demo.example"],
        "phone": ["9234567802"],
        "pan": ["ASDFG5678H"],
        "aadhaar": [],
        "bank": ["640012345678"],
        "ifsc": ["MERD0000456"],
        "government_id": ["GOV-ID-IND-482739"],
        "credit_card": ["4532123412341234"],
    },
    "03_University_Student_Report.pdf": {
        "email": ["ananya.rao@lakeside-demo.example"],
        "phone": ["9345678903"],
        "pan": ["HJKLO2468P"],
        "aadhaar": [],
        "bank": ["720045678901"],
        "ifsc": ["LKIT0000789"],
        "government_id": ["EDU-ID-593821"],
        "credit_card": [],
    },
    "04_Hospital_Administration_Report.pdf": {
        "email": ["kavya.sharma@greenfield-demo.example"],
        "phone": ["9456789012"],
        "pan": [],
        "aadhaar": [],
        "bank": ["830056789012"],
        "ifsc": ["GFMC0000321"],
        "government_id": ["HOSP-ID-704215"],
        "credit_card": [],
    },
    "05_Business_Project_Report.pdf": {
        "email": ["vikram.patel@blueriver-demo.example"],
        "phone": ["9567890123"],
        "pan": [],
        "aadhaar": [],
        "bank": ["910067890123"],
        "ifsc": ["BLRA0000567"],
        "government_id": ["CLIENT-ID-618402"],
        "credit_card": ["5555666677778884"],
    },
}


def flatten_regex(findings):
    values = []
    for items in findings.values():
        values.extend(items)
    return list(dict.fromkeys(values))


def flatten_ner(findings):
    values = []
    for label in ("PERSON", "ORG", "GPE", "LOC", "MONEY"):
        values.extend(findings.get(label, []))
    return list(dict.fromkeys(values))


def contains(text, value):
    return value.lower() in text.lower()


def retrieved_ground_truth(gt, raw_context):
    found = []
    for category, values in gt.items():
        for value in values:
            if contains(raw_context, value):
                found.append((category, value))
    return found


def predicted_matches(predicted, gt_pairs):
    """
    A prediction is correct when it exactly matches a known ground-truth
    structured PII value. NER entities such as names/organizations are
    reported separately because the structured ground truth does not
    define every contextual entity.
    """
    gt_values = {value.lower() for _, value in gt_pairs}
    return [p for p in predicted if p.lower() in gt_values]


def main():
    print("=" * 78)
    print("PRIVACY-AWARE RAG: 5 DOCUMENT / 20 QUERY EXPERIMENT")
    print("=" * 78)

    # Verify all PDFs exist.
    missing = [str(p) for p in DOCUMENTS if not p.exists()]
    if missing:
        print("\nERROR: These PDFs were not found:")
        for p in missing:
            print(" ", p)
        return

    rows = []

    total_gt = 0
    total_correct = 0
    total_predicted = 0
    baseline_leakage = 0
    proposed_leakage = 0

    baseline_times = []
    proposed_times = []
    chunk_counts = {}

    for doc_index, pdf in enumerate(DOCUMENTS):
        print(f"\n{'=' * 78}")
        print(f"DOCUMENT {doc_index + 1}: {pdf.name}")
        print(f"{'=' * 78}")

        # Index this document into the current Chroma collection.
        docs = load_and_split_pdf(str(pdf))
        chunk_counts[pdf.name] = len(docs)
        create_vector_store(docs, reset=True)

        gt = GROUND_TRUTH[pdf.name]

        for local_index in range(4):
            query_number = doc_index * 4 + local_index + 1
            query = QUERIES[doc_index * 4 + local_index]

            # Baseline timing: retrieval only.
            t0 = time.perf_counter()
            retrieval = get_relevant_context(query, k=3)
            baseline_ms = (time.perf_counter() - t0) * 1000

            raw_context = retrieval["context"]
            retrieved_gt = retrieved_ground_truth(gt, raw_context)

            # Proposed timing: retrieval + Regex + NER + redaction.
            t1 = time.perf_counter()
            guard = process_context(raw_context)
            proposed_ms = (time.perf_counter() - t1) * 1000 + baseline_ms

            safe_context = guard["safe_context"]
            remaining_gt = retrieved_ground_truth(gt, safe_context)

            regex_values = flatten_regex(guard["regex_findings"])
            ner_values = flatten_ner(guard["ner_findings"])
            predictions = list(dict.fromkeys(regex_values + ner_values))

            correct = predicted_matches(predictions, retrieved_gt)

            total_gt += len(retrieved_gt)
            total_correct += len(correct)
            total_predicted += len(predictions)

            baseline_leakage += len(retrieved_gt)
            proposed_leakage += len(remaining_gt)

            baseline_times.append(baseline_ms)
            proposed_times.append(proposed_ms)

            rows.append({
                "query_no": query_number,
                "document": pdf.name,
                "query": query,
                "retrieved_pii": len(retrieved_gt),
                "detected_predictions": len(predictions),
                "correct_structured_detections": len(correct),
                "remaining_pii_after_redaction": len(remaining_gt),
                "baseline_latency_ms": round(baseline_ms, 2),
                "proposed_latency_ms": round(proposed_ms, 2),
                "action": guard["action"],
            })

            print(f"\nQ{query_number}: {query}")
            print(f"  Retrieved PII: {len(retrieved_gt)}")
            print(f"  Correct structured detections: {len(correct)}")
            print(f"  Remaining PII: {len(remaining_gt)}")
            print(f"  Baseline retrieval: {baseline_ms:.2f} ms")
            print(f"  Proposed retrieval + guardrail: {proposed_ms:.2f} ms")

    precision = total_correct / total_predicted if total_predicted else 0
    recall = total_correct / total_gt if total_gt else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    baseline_rate = (
        baseline_leakage / baseline_leakage * 100
        if baseline_leakage else 0
    )
    proposed_rate = (
        proposed_leakage / baseline_leakage * 100
        if baseline_leakage else 0
    )
    reduction = (
        (baseline_leakage - proposed_leakage) / baseline_leakage * 100
        if baseline_leakage else 0
    )

    mean_baseline = (
        sum(baseline_times) / len(baseline_times)
        if baseline_times else 0
    )
    mean_proposed = (
        sum(proposed_times) / len(proposed_times)
        if proposed_times else 0
    )
    overhead = (
        (mean_proposed - mean_baseline) / mean_baseline * 100
        if mean_baseline else 0
    )

    print("\n" + "=" * 78)
    print("FINAL MEASURED RESULTS")
    print("=" * 78)
    print(f"Documents                         : {len(DOCUMENTS)}")
    print(f"Queries                           : {len(rows)}")
    print(f"Chunk counts                      : {chunk_counts}")
    print(f"Total retrieved GT PII instances : {total_gt}")
    print(f"Correct detections                : {total_correct}")
    print(f"Predicted detections              : {total_predicted}")
    print(f"Precision                         : {precision * 100:.2f}%")
    print(f"Recall                            : {recall * 100:.2f}%")
    print(f"F1-score                          : {f1 * 100:.2f}%")
    print(f"Baseline PII forwarded/leaked    : {baseline_leakage}")
    print(f"Proposed PII remaining            : {proposed_leakage}")
    print(f"Baseline leakage rate             : {baseline_rate:.2f}%")
    print(f"Proposed leakage rate             : {proposed_rate:.2f}%")
    print(f"Leakage reduction                 : {reduction:.2f}%")
    print(f"Mean baseline retrieval           : {mean_baseline:.2f} ms")
    print(f"Mean proposed retrieval+guardrail : {mean_proposed:.2f} ms")
    print(f"Guardrail overhead                : {overhead:.2f}%")

    csv_path = Path("experiment_results.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    summary_path = Path("experiment_summary.txt")
    summary_path.write_text(
        "\n".join([
            "PRIVACY-AWARE RAG EXPERIMENT SUMMARY",
            f"Documents: {len(DOCUMENTS)}",
            f"Queries: {len(rows)}",
            f"Precision: {precision * 100:.2f}%",
            f"Recall: {recall * 100:.2f}%",
            f"F1-score: {f1 * 100:.2f}%",
            f"Baseline PII leakage: {baseline_leakage}",
            f"Proposed PII remaining: {proposed_leakage}",
            f"Baseline leakage rate: {baseline_rate:.2f}%",
            f"Proposed leakage rate: {proposed_rate:.2f}%",
            f"Leakage reduction: {reduction:.2f}%",
            f"Mean baseline retrieval: {mean_baseline:.2f} ms",
            f"Mean proposed retrieval+guardrail: {mean_proposed:.2f} ms",
            f"Guardrail overhead: {overhead:.2f}%",
        ]),
        encoding="utf-8",
    )

    print(f"\nDetailed CSV: {csv_path.resolve()}")
    print(f"Summary TXT : {summary_path.resolve()}")
    print("\nThese values are measured from your local implementation.")
    print("Do not copy any old/fabricated numbers from the manuscript.")


if __name__ == "__main__":
    main()
