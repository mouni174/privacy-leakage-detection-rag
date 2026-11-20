"""Privacy telemetry for the latest guarded RAG query."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.ui import (
    apply_global_styles,
    render_empty_state,
    render_page_header,
    render_section_heading,
    render_sidebar_brand,
    sanitize_sensitive_text,
)

load_dotenv()

st.set_page_config(
    page_title="Privacy Dashboard | Privacy Leakage Detection",
    page_icon=":material/shield:",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

result = st.session_state.get("last_query_result")
audit_log = st.session_state.audit_log

if result:
    action = result["action"]
    state_label = f"Latest decision · {action}"
else:
    state_label = "Awaiting query telemetry"

render_page_header(
    title="Privacy protection center",
    description=(
        "Inspect the latest query's detection coverage, guardrail decision, and "
        "source attribution. Findings are shown as categories and counts, never "
        "as sensitive values."
    ),
    eyebrow="03 / Detection telemetry",
    icon="shield",
    status_label=state_label,
)

st.space("medium")

total_documents = len(st.session_state.documents)
total_chunks_retrieved = sum(
    int(record.get("Retrieved Chunk Count", 0) or 0) for record in audit_log
)
regex_detections = sum(
    int(record.get("Regex Finding Count", 0) or 0) for record in audit_log
)
ner_detections = sum(
    int(record.get("NER Finding Count", 0) or 0) for record in audit_log
)
confirmed_entities = sum(
    int(record.get("Total Sensitive Items", 0) or 0) for record in audit_log
)
redacted_entities = sum(
    int(record.get("Redacted Entity Count", 0) or 0) for record in audit_log
)
blocked_requests = sum(
    record.get("Guardrail Action") == "Blocked" for record in audit_log
)
latencies = [
    float(record["Query Processing Latency (ms)"])
    for record in audit_log
    if record.get("Query Processing Latency (ms)") is not None
]
average_query_latency = sum(latencies) / len(latencies) if latencies else None

render_section_heading(
    "Session reliability",
    "Aggregated counts from this Streamlit session; sensitive values are not displayed.",
)
with st.container(horizontal=True):
    st.metric("Documents processed", total_documents, border=True)
    st.metric("Chunks retrieved", total_chunks_retrieved, border=True)
    st.metric("Regex detections", regex_detections, border=True)
    st.metric("NER detections", ner_detections, border=True)
with st.container(horizontal=True):
    st.metric("Confirmed sensitive entities", confirmed_entities, border=True)
    st.metric("Redacted entities", redacted_entities, border=True)
    st.metric("Blocked requests", blocked_requests, border=True)
    st.metric(
        "Mean query processing",
        "—" if average_query_latency is None else f"{average_query_latency:.1f} ms",
        border=True,
    )

evaluation_path = Path(__file__).parents[1] / "reports" / "phase5_evaluation.json"
st.space("small")
render_section_heading(
    "Offline evaluation",
    "Metrics below are computed from the checked-in synthetic evaluation corpus, not live user data.",
)
if evaluation_path.exists():
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    detection_report = evaluation["detection"]
    detection_rows = [
        {
            "Configuration": configuration,
            "Precision": metrics["precision"],
            "Recall": metrics["recall"],
            "F1": metrics["f1"],
            "FPR": metrics["fpr"],
            "TP": metrics["tp"],
            "FP": metrics["fp"],
            "FN": metrics["fn"],
            "TN": metrics["tn"],
        }
        for configuration, metrics in detection_report.items()
    ]
    with st.container(border=True):
        st.markdown("### Detection performance")
        st.dataframe(
            pd.DataFrame(detection_rows),
            hide_index=True,
            width="stretch",
        )
        st.bar_chart(
            pd.DataFrame(detection_rows).set_index("Configuration")[
                ["Precision", "Recall", "F1", "FPR"]
            ],
            height=280,
        )

    retrieval_report = evaluation["retrieval"]
    retrieval_rows = [
        {"Metric": "Precision@K", "Score": retrieval_report["precision_at_k"]},
        {"Metric": "Recall@K", "Score": retrieval_report["recall_at_k"]},
        {"Metric": "MRR", "Score": retrieval_report["mean_reciprocal_rank"]},
        {
            "Metric": "Irrelevant rate",
            "Score": retrieval_report["irrelevant_retrieval_rate_after_filtering"],
        },
        {
            "Metric": "Raw duplicate rate",
            "Score": retrieval_report["duplicate_retrieval_rate_raw_top_k"],
        },
    ]
    with st.container(border=True):
        st.markdown("### Held-out retrieval quality")
        st.caption(
            f"K={retrieval_report['k']} · distance cutoff "
            f"{retrieval_report['threshold_l2']:.6f} calibrated on a separate "
            "synthetic query split"
        )
        st.bar_chart(
            pd.DataFrame(retrieval_rows).set_index("Metric"),
            height=260,
        )

    latency_rows = [
        {
            "Component": configuration,
            "Mean ms": metrics["mean_ms"],
            "Median ms": metrics["median_ms"],
            "P95 ms": metrics["p95_ms"],
        }
        for configuration, metrics in evaluation["detection_latency"].items()
    ]
    latency_rows.append(
        {
            "Component": "Chroma retrieval",
            "Mean ms": retrieval_report["chroma_query_latency_ms"]["mean"],
            "Median ms": retrieval_report["chroma_query_latency_ms"]["median"],
            "P95 ms": retrieval_report["chroma_query_latency_ms"]["p95"],
        }
    )
    with st.container(border=True):
        st.markdown("### Local processing latency")
        st.dataframe(pd.DataFrame(latency_rows), hide_index=True, width="stretch")
        st.metric(
            "Synthetic corpus redaction leakage",
            f"{evaluation['privacy_leakage']['unredacted_sensitive_spans']} / "
            f"{evaluation['privacy_leakage']['sensitive_gold_spans']}",
            border=True,
        )
else:
    st.info(
        "The offline evaluation report has not been generated. Run "
        "`python scripts/evaluate_phase5.py` to build it."
    )

if not result:
    render_empty_state(
        eyebrow="LIVE DETECTION FEED",
        title="No query telemetry yet",
        description=(
            "This dashboard fills with real Regex and NER results after a guarded "
            "query runs. Counts and categories come from that evaluation; no sample "
            "findings are generated."
        ),
        icon="radar",
        steps=(
            "Index a PDF if the workspace is still empty.",
            "Run a query with your selected privacy policy.",
            "Return here to review the guardrail decision and detection totals.",
        ),
        actions=(
            (
                "pages/1_Document_Management.py",
                "Manage Documents",
                "folder_managed",
            ),
            ("pages/2_RAG_Query.py", "Open Secure RAG Query", "forum"),
        ),
    )

    if audit_log:
        st.space("small")
        render_section_heading(
            "Session activity",
            "Counts below are calculated from this session's actual audit records.",
        )
        total_queries = len(audit_log)
        total_blocked = sum(
            1 for entry in audit_log if entry.get("Guardrail Action") == "Blocked"
        )
        total_redacted = sum(
            1 for entry in audit_log if entry.get("Guardrail Action") == "Redacted"
        )
        total_allowed = sum(
            1 for entry in audit_log if entry.get("Guardrail Action") == "Allowed"
        )

        with st.container(horizontal=True):
            st.metric("Queries processed", total_queries, border=True)
            st.metric("Blocked", total_blocked, border=True)
            st.metric("Redacted", total_redacted, border=True)
            st.metric("Allowed", total_allowed, border=True)
    st.stop()

guardrail = result["guardrail"]
regex_findings = {
    category.replace("_", " ").title(): values
    for category, values in guardrail.get("regex_findings", {}).items()
    if values
}
ner_findings = {
    category: values
    for category, values in guardrail.get("ner_findings", {}).items()
    if values
}
safe_scope = (
    sanitize_sensitive_text(result.get("target_scope", ""))
    if result.get("target_scope") != "All Documents"
    else "All Documents"
)

render_section_heading(
    "Latest inspection",
    f"Evaluated {result['timestamp']} · scope: {safe_scope} · "
    f"policy: {result['privacy_policy']}",
)

inspection_column, decision_column = st.columns([1.45, 0.9], gap="large")
with inspection_column:
    with st.container(border=True):
        st.markdown('<div class="pld-story-index">SANITIZED REQUEST</div>', unsafe_allow_html=True)
        st.markdown("### :material/search_check: Query under inspection")
        st.markdown(
            f"> {sanitize_sensitive_text(result.get('sanitized_query', '[Query unavailable]'))}"
        )
        st.caption(
            f"{sum(row.get('Retrieved chunks', 0) for row in result.get('source_attribution', []))} "
            "retrieved chunk(s) · "
            "raw query and source text are not displayed in this report"
        )

with decision_column:
    with st.container(border=True):
        st.markdown('<div class="pld-story-index">GUARDRAIL DECISION</div>', unsafe_allow_html=True)
        action_color = {
            "Blocked": "red",
            "Redacted": "orange",
            "Allowed": "green",
        }.get(result["action"], "gray")
        st.badge(result["action"], color=action_color)
        st.markdown(f"### {result['risk_badge']}")
        st.caption(result["risk_desc"])
        st.metric("Sensitive findings", result["total_sensitive"], border=True)
        detection_totals = st.columns(2, gap="small")
        with detection_totals[0]:
            st.metric("Regex", result["regex_count"], border=True)
        with detection_totals[1]:
            st.metric("NER", result["ner_count"], border=True)

st.space("small")
render_section_heading(
    "Detection coverage",
    "Confirmed sensitive findings from the latest guardrail evaluation. Uncertain candidates are not treated as PII or blocking triggers.",
)

detection_columns = st.columns(2, gap="large")
with detection_columns[0]:
    with st.container(border=True):
        st.markdown("### :material/regex: Pattern detection")
        st.caption("Validated structured identifiers and context-confirmed numeric matches")
        if regex_findings:
            for category, finding_count in regex_findings.items():
                st.markdown(f"- **{category}** · {finding_count} finding(s)")
        else:
            st.success("No confirmed regex PII was detected.")

with detection_columns[1]:
    with st.container(border=True):
        st.markdown("### :material/psychology: Entity detection")
        st.caption("Context-classified spaCy entities; ordinary names and organizations are not automatically sensitive")
        if ner_findings:
            for category, finding_count in ner_findings.items():
                st.markdown(f"- **{category}** · {finding_count} finding(s)")
        else:
            st.success("No confirmed NER-based PII was detected.")

st.space("small")
render_section_heading(
    "Source attribution",
    "Per-document counts for findings present in retrieved chunks; sensitive values are omitted.",
)

source_rows = result.get("source_attribution", [])
if source_rows:
    with st.container(border=True):
        st.dataframe(
            source_rows,
            hide_index=True,
            width="stretch",
            column_config={
                "Source document": st.column_config.TextColumn(
                    "Source document", width="large"
                ),
                "Retrieved chunks": st.column_config.NumberColumn(
                    "Chunks", width="small"
                ),
                "Regex findings": st.column_config.NumberColumn(
                    "Regex", width="small"
                ),
                "NER findings": st.column_config.NumberColumn(
                    "NER", width="small"
                ),
                "Assessment": st.column_config.TextColumn(
                    "Assessment", width="medium"
                ),
            },
        )
else:
    st.info("No source chunks were returned for attribution.")

st.space("small")
render_section_heading(
    "Guardrail outcome",
    "Confirmed personal identifiers in both the question and retrieved context are covered by the active policy.",
)

with st.container(border=True):
    if result["action"] == "Blocked":
        st.error(
            "Transmission was blocked. The question and retrieved text are suppressed "
            "and no content was sent to Gemini."
        )
    elif result["action"] == "Redacted":
        st.badge(
            "Redacted before generation",
            icon=":material/verified_user:",
            color="orange",
        )
        st.info(
            "The guardrail supplied a sanitized question and context for generation. "
            "Source text and matched values are intentionally not displayed."
        )
    else:
        st.success(
            "No confirmed sensitive values were flagged. Source context is not "
            "displayed in the dashboard to avoid exposing document text."
        )

    st.caption(result.get("policy_rationale", "No policy rationale was recorded."))

st.page_link(
    "pages/4_Privacy_Audit.py",
    label="Review privacy audit trail",
    width="content",
)
