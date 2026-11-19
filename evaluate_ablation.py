import csv
import time
from pathlib import Path

from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store
from src.retriever import get_relevant_context
from src.privacy_detector import scan_sensitive_data
from src.ner_detector import detect_entities


# ============================================================
# PATHS
# ============================================================

BASE = Path(r"C:\Users\tmoun\Downloads")

DOCUMENTS = [
    BASE / "01_HR_Employee_Report.pdf",
    BASE / "02_Banking_Finance_Report.pdf",
    BASE / "03_University_Student_Report.pdf",
    BASE / "04_Hospital_Administration_Report.pdf",
    BASE / "05_Business_Project_Report.pdf",
]


# ============================================================
# 20 QUERIES
# ============================================================

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
    "What billing and reimbursement information was recorded?",

    "What organization does Vikram Patel represent?",
    "What contact information is listed for the client?",
    "Who are the members of the implementation team?",
    "What financial and procurement information is included in the report?",
]


# ============================================================
# GROUND TRUTH
# ============================================================

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


# ============================================================
# HELPERS
# ============================================================

def flatten_regex(findings):
    values = []

    if isinstance(findings, dict):
        for items in findings.values():
            if isinstance(items, list):
                values.extend(items)

    return list(dict.fromkeys(values))


def flatten_ner(findings):
    values = []

    if isinstance(findings, dict):
        for label in ("PERSON", "ORG", "GPE", "LOC", "DATE", "MONEY"):
            items = findings.get(label, [])
            if isinstance(items, list):
                values.extend(items)

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
    gt_values = {value.lower() for _, value in gt_pairs}

    return [
        p for p in predicted
        if p.lower() in gt_values
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("ABLATION STUDY")
    print("5 DOCUMENTS / 20 QUERIES")
    print("=" * 80)

    # Check PDFs
    missing = [str(p) for p in DOCUMENTS if not p.exists()]

    if missing:
        print("\nERROR: These PDFs were not found:")

        for p in missing:
            print(" ", p)

        return

    # --------------------------------------------------------
    # Storage for each configuration
    # --------------------------------------------------------

    configs = {
        "Standard RAG": {
            "gt": 0,
            "correct": 0,
            "predicted": 0,
            "remaining": 0,
            "times": [],
        },

        "Regex only": {
            "gt": 0,
            "correct": 0,
            "predicted": 0,
            "remaining": 0,
            "times": [],
        },

        "NER only": {
            "gt": 0,
            "correct": 0,
            "predicted": 0,
            "remaining": 0,
            "times": [],
        },

        "Regex + NER": {
            "gt": 0,
            "correct": 0,
            "predicted": 0,
            "remaining": 0,
            "times": [],
        },
    }

    rows = []

    # ========================================================
    # PROCESS ALL DOCUMENTS
    # ========================================================

    for doc_index, pdf in enumerate(DOCUMENTS):

        print("\n" + "=" * 80)
        print(f"DOCUMENT {doc_index + 1}: {pdf.name}")
        print("=" * 80)

        # ----------------------------------------------------
        # Index current PDF
        # ----------------------------------------------------

        docs = load_and_split_pdf(str(pdf))

        print(f"Chunks: {len(docs)}")

        create_vector_store(docs)

        gt = GROUND_TRUTH[pdf.name]

        # ----------------------------------------------------
        # Four queries for this document
        # ----------------------------------------------------

        for local_index in range(4):

            query_number = doc_index * 4 + local_index + 1

            query = QUERIES[
                doc_index * 4 + local_index
            ]

            print(f"\nQ{query_number}: {query}")

            # =================================================
            # RETRIEVAL
            # =================================================

            t0 = time.perf_counter()

            retrieval = get_relevant_context(
                query,
                k=3
            )

            retrieval_ms = (
                time.perf_counter() - t0
            ) * 1000

            # IMPORTANT:
            # get_relevant_context returns a dictionary.
            # We need the actual text.
            raw_context = retrieval["context"]

            if not isinstance(raw_context, str):
                raw_context = str(raw_context)

            # =================================================
            # GROUND-TRUTH PII PRESENT IN RETRIEVED CONTEXT
            # =================================================

            retrieved_gt = retrieved_ground_truth(
                gt,
                raw_context
            )

            gt_count = len(retrieved_gt)

            # =================================================
            # REGEX DETECTION
            # =================================================

            regex_findings = scan_sensitive_data(
                raw_context
            )

            regex_values = flatten_regex(
                regex_findings
            )

            # =================================================
            # NER DETECTION
            # =================================================

            ner_findings = detect_entities(
                raw_context
            )

            ner_values = flatten_ner(
                ner_findings
            )

            # =================================================
            # STANDARD RAG
            # =================================================

            configs["Standard RAG"]["gt"] += gt_count
            configs["Standard RAG"]["remaining"] += gt_count
            configs["Standard RAG"]["times"].append(
                retrieval_ms
            )

            # =================================================
            # REGEX ONLY
            # =================================================

            regex_correct = predicted_matches(
                regex_values,
                retrieved_gt
            )

            regex_correct_count = len(
                regex_correct
            )

            regex_remaining = max(
                gt_count - regex_correct_count,
                0
            )

            configs["Regex only"]["gt"] += gt_count
            configs["Regex only"]["correct"] += (
                regex_correct_count
            )
            configs["Regex only"]["predicted"] += (
                len(regex_values)
            )
            configs["Regex only"]["remaining"] += (
                regex_remaining
            )
            configs["Regex only"]["times"].append(
                retrieval_ms
            )

            # =================================================
            # NER ONLY
            # =================================================

            ner_correct = predicted_matches(
                ner_values,
                retrieved_gt
            )

            ner_correct_count = len(
                ner_correct
            )

            ner_remaining = max(
                gt_count - ner_correct_count,
                0
            )

            configs["NER only"]["gt"] += gt_count
            configs["NER only"]["correct"] += (
                ner_correct_count
            )
            configs["NER only"]["predicted"] += (
                len(ner_values)
            )
            configs["NER only"]["remaining"] += (
                ner_remaining
            )
            configs["NER only"]["times"].append(
                retrieval_ms
            )

            # =================================================
            # REGEX + NER
            # =================================================

            combined_values = list(
                dict.fromkeys(
                    regex_values + ner_values
                )
            )

            combined_correct = predicted_matches(
                combined_values,
                retrieved_gt
            )

            combined_correct_count = len(
                combined_correct
            )

            combined_remaining = max(
                gt_count - combined_correct_count,
                0
            )

            configs["Regex + NER"]["gt"] += (
                gt_count
            )
            configs["Regex + NER"]["correct"] += (
                combined_correct_count
            )
            configs["Regex + NER"]["predicted"] += (
                len(combined_values)
            )
            configs["Regex + NER"]["remaining"] += (
                combined_remaining
            )
            configs["Regex + NER"]["times"].append(
                retrieval_ms
            )

            # =================================================
            # PRINT QUERY RESULT
            # =================================================

            print(
                f"  Retrieved GT PII : {gt_count}"
            )

            print(
                f"  Regex detections  : {len(regex_values)}"
            )

            print(
                f"  NER detections    : {len(ner_values)}"
            )

            print(
                f"  Retrieval latency : {retrieval_ms:.2f} ms"
            )

            # =================================================
            # SAVE QUERY DATA
            # =================================================

            rows.append({
                "query_no": query_number,
                "document": pdf.name,
                "query": query,
                "ground_truth": gt_count,
                "regex_predictions": len(regex_values),
                "regex_correct": regex_correct_count,
                "regex_remaining": regex_remaining,
                "ner_predictions": len(ner_values),
                "ner_correct": ner_correct_count,
                "ner_remaining": ner_remaining,
                "combined_predictions": len(combined_values),
                "combined_correct": combined_correct_count,
                "combined_remaining": combined_remaining,
                "latency_ms": round(
                    retrieval_ms,
                    2
                ),
            })

    # ========================================================
    # FINAL METRICS
    # ========================================================

    print("\n")
    print("=" * 100)
    print("FINAL ABLATION RESULTS")
    print("=" * 100)

    summary_rows = []

    for name, data in configs.items():

        gt = data["gt"]
        correct = data["correct"]
        predicted = data["predicted"]
        remaining = data["remaining"]

        # Standard RAG has no detector predictions.
        if name == "Standard RAG":
            precision = 0
            recall = 0
            f1 = 0
        else:

            precision = (
                correct / predicted
                if predicted
                else 0
            )

            recall = (
                correct / gt
                if gt
                else 0
            )

            f1 = (
                2 * precision * recall
                / (precision + recall)
                if precision + recall
                else 0
            )

        leakage_rate = (
            remaining / gt * 100
            if gt
            else 0
        )

        mean_latency = (
            sum(data["times"])
            / len(data["times"])
            if data["times"]
            else 0
        )

        summary_rows.append({
            "Configuration": name,
            "Ground Truth PII": gt,
            "Correct": correct,
            "Predicted": predicted,
            "Precision (%)": precision * 100,
            "Recall (%)": recall * 100,
            "F1 (%)": f1 * 100,
            "PII Remaining": remaining,
            "Leakage Rate (%)": leakage_rate,
            "Mean Latency (ms)": mean_latency,
        })

        print(f"\n{name}")
        print("-" * 50)
        print(f"Ground Truth PII : {gt}")
        print(f"Correct           : {correct}")
        print(f"Predicted         : {predicted}")
        print(f"Precision         : {precision * 100:.2f}%")
        print(f"Recall            : {recall * 100:.2f}%")
        print(f"F1-score          : {f1 * 100:.2f}%")
        print(f"PII Remaining     : {remaining}")
        print(f"Leakage Rate      : {leakage_rate:.2f}%")
        print(f"Mean Latency      : {mean_latency:.2f} ms")

    # ========================================================
    # SAVE CSV
    # ========================================================

    detailed_path = Path(
        "ablation_detailed_results.csv"
    )

    with detailed_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)

    summary_path = Path(
        "ablation_summary_results.csv"
    )

    with summary_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=summary_rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(summary_rows)

    print("\n")
    print("=" * 80)
    print("FILES CREATED")
    print("=" * 80)
    print(
        f"Detailed: {detailed_path.resolve()}"
    )
    print(
        f"Summary : {summary_path.resolve()}"
    )


if __name__ == "__main__":
    main()