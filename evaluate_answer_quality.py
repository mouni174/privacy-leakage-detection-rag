import csv
from pathlib import Path

from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.llm import generate_answer


BASE = Path(r"C:\Users\tmoun\Downloads")


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


def main():

    print("=" * 78)
    print("ANSWER QUALITY EVALUATION")
    print("5 DOCUMENTS / 20 QUESTIONS")
    print("=" * 78)

    rows = []

    for doc_index, pdf in enumerate(DOCUMENTS):

        print("\n" + "=" * 78)
        print(f"DOCUMENT {doc_index + 1}: {pdf.name}")
        print("=" * 78)

        if not pdf.exists():
            print(f"ERROR: PDF not found: {pdf}")
            return

        # Load and index current document.
        docs = load_and_split_pdf(str(pdf))

        print(f"Chunks created: {len(docs)}")

        create_vector_store(docs)

        # Four questions per document.
        for local_index in range(4):

            question_index = (
                doc_index * 4 + local_index
            )

            question_number = question_index + 1

            question = QUERIES[question_index]

            print("\n" + "-" * 78)
            print(f"Q{question_number}: {question}")
            print("-" * 78)

            # ---------------------------------------------------------
            # Retrieve top-3 context.
            # ---------------------------------------------------------

            retrieval = get_relevant_context(
                question,
                k=3
            )

            raw_context = retrieval["context"]

            # ---------------------------------------------------------
            # Standard RAG
            # Raw retrieved context -> Gemini
            # ---------------------------------------------------------

            print("Generating Standard RAG answer...")

            standard_answer = generate_answer(
                raw_context,
                question
            )

            # ---------------------------------------------------------
            # Privacy-Aware RAG
            # Retrieved context -> Guardrail -> Gemini
            # ---------------------------------------------------------

            print("Applying privacy guardrail...")

            guard = process_context(
                raw_context
            )

            safe_context = guard["safe_context"]

            print("Generating Privacy-Aware RAG answer...")

            privacy_answer = generate_answer(
                safe_context,
                question
            )

            # ---------------------------------------------------------
            # Save results.
            # ---------------------------------------------------------

            rows.append({
                "question_no": question_number,
                "document": pdf.name,
                "question": question,
                "standard_rag_answer": standard_answer,
                "privacy_aware_rag_answer": privacy_answer,
            })

            print("\nSTANDARD RAG ANSWER:")
            print(standard_answer)

            print("\nPRIVACY-AWARE RAG ANSWER:")
            print(privacy_answer)

            print("\nAnswer pair saved.")

    # -------------------------------------------------------------
    # Save CSV
    # -------------------------------------------------------------

    output_path = Path(
        "answer_quality_results.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "question_no",
                "document",
                "question",
                "standard_rag_answer",
                "privacy_aware_rag_answer",
                "standard_correctness",
                "privacy_correctness",
                "standard_relevance",
                "privacy_relevance",
                "standard_completeness",
                "privacy_completeness",
            ]
        )

        writer.writeheader()

        for row in rows:

            row["standard_correctness"] = ""
            row["privacy_correctness"] = ""

            row["standard_relevance"] = ""
            row["privacy_relevance"] = ""

            row["standard_completeness"] = ""
            row["privacy_completeness"] = ""

            writer.writerow(row)

    print("\n" + "=" * 78)
    print("ANSWER QUALITY EVALUATION COMPLETED")
    print("=" * 78)

    print(
        f"Questions evaluated: {len(rows)}"
    )

    print(
        f"Results saved to: "
        f"{output_path.resolve()}"
    )

    print(
        "\nOpen answer_quality_results.csv "
        "and rate each answer from 1 to 5."
    )


if __name__ == "__main__":
    main()