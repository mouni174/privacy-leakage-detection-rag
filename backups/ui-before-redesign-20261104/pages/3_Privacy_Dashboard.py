"""
pages/3_Privacy_Dashboard.py
-----------------------------
Feature 4 – Privacy Dashboard & Detection Telemetry.

Purpose: Monitor privacy detections and guardrail decisions.
Includes:
  • Total sensitive items detected
  • Regex findings
  • NER findings
  • Detected PII categories
  • Privacy risk status
  • Guardrail action
  • Structured detection report
  • Source-document attribution

Uses the latest query results from session state and does not invent statistics.
"""

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Privacy Dashboard – Privacy RAG",
    page_icon="🛡️",
    layout="wide"
)

# ── Session state ──────────────────────────────────────────────────────────────
init_session_state()

# ── Page title & description ───────────────────────────────────────────────────
st.title("🛡️ Privacy Dashboard")
st.markdown(
    "Real-time telemetry and structured threat reports for retrieved context. "
    "Metrics reflect the **latest query evaluation** performed on the **RAG Query** page."
)

st.markdown("---")

res = st.session_state.get("last_query_result")

# ── Empty state: No queries run yet ────────────────────────────────────────────
if not res:
    st.info(
        "📭 **No query telemetry available.** "
        "Navigate to **🔍 RAG Query** in the sidebar to ask a question and inspect live detection results."
    )

    # Show session historical summary if queries were run previously
    if st.session_state.audit_log:
        st.markdown("---")
        st.subheader("📊 Session Activity Summary")
        total_queries = len(st.session_state.audit_log)
        total_blocked = sum(1 for a in st.session_state.audit_log if a["Guardrail Action"] == "Blocked")
        total_redacted = sum(1 for a in st.session_state.audit_log if a["Guardrail Action"] == "Redacted")
        total_allowed = sum(1 for a in st.session_state.audit_log if a["Guardrail Action"] == "Allowed")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Queries Processed", total_queries)
        m2.metric("Blocked Requests 🔴", total_blocked)
        m3.metric("Redacted Requests 🟡", total_redacted)
        m4.metric("Allowed Requests 🟢", total_allowed)

    st.stop()

# ── Query Header Context ───────────────────────────────────────────────────────
st.subheader("🔍 Evaluated Query Context")

q_col1, q_col2, q_col3 = st.columns([2, 1, 1])
with q_col1:
    st.markdown(f"**Question:** `{res['question']}`")
with q_col2:
    st.markdown(f"**Target Scope:** `{res['target_scope']}`")
with q_col3:
    st.markdown(f"**Policy:** `{res['privacy_policy']}`")

st.caption(f"Evaluated at {res['timestamp']}")

st.markdown("---")

# ── KPI Metrics ────────────────────────────────────────────────────────────────
st.subheader("📊 Privacy KPIs & Guardrail Action")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Sensitive Items Detected", res["total_sensitive"])
kpi2.metric("Regex Findings", res["regex_count"])
kpi3.metric("NER Findings", res["ner_count"])
kpi4.metric("Guardrail Action", res["action"])
kpi5.metric("Privacy Risk Status", res["risk_badge"])

# Risk status alert banner
if res["risk_status"].startswith("🟢"):
    st.success(f"**Privacy Risk Assessment:** {res['risk_status']} — {res['risk_desc']}")
elif res["risk_status"].startswith("🟡"):
    st.warning(f"**Privacy Risk Assessment:** {res['risk_status']} — {res['risk_desc']}")
else:
    st.error(f"**Privacy Risk Assessment:** {res['risk_status']} — {res['risk_desc']}")

st.markdown("---")

# ── Detected PII Categories ────────────────────────────────────────────────────
st.subheader("🏷️ Detected PII Categories")

guardrail = res["guardrail"]
active_regex = {
    k.replace("_", " ").title(): v
    for k, v in guardrail.get("regex_findings", {}).items()
    if v
}
active_ner = {
    k: v
    for k, v in guardrail.get("ner_findings", {}).items()
    if v
}

if not active_regex and not active_ner:
    st.success("✅ **Zero PII Categories Detected:** The retrieved context contains no sensitive identifiers.")
else:
    cat_items = []
    for k, v in active_regex.items():
        cat_items.append(f"**{k}** ({len(v)})")
    for k, v in active_ner.items():
        cat_items.append(f"**{k}** ({len(v)})")

    st.markdown(" | ".join(cat_items))

st.markdown("---")

# ── Source Document Attribution Helper ─────────────────────────────────────────
documents = res.get("documents", [])

def get_finding_sources(item_str: str) -> list:
    """Return list of source document names containing the sensitive item."""
    sources = set()
    if documents:
        for doc in documents:
            if item_str in doc.page_content:
                sources.add(doc.metadata.get("source_doc", "Document"))
    return sorted(list(sources)) if sources else ["Retrieved Context"]

# ── Structured Detection Report & Source Attribution ───────────────────────────
st.subheader("📋 Structured Detection Report")

col_det1, col_det2 = st.columns(2)

with col_det1:
    st.markdown("#### 🔍 Structured Patterns (Regex)")
    if active_regex:
        for category, items in active_regex.items():
            st.markdown(f"**{category}** ({len(items)} found):")
            for item in items:
                srcs = ", ".join(get_finding_sources(item))
                st.markdown(f"- `{item}` — *Source: {srcs}*")
    else:
        st.info("No pattern-based PII (SSN, Email, Phone, PAN, Card) detected.")

with col_det2:
    st.markdown("#### 🧠 Contextual Entities (NER)")
    if active_ner:
        for label, items in active_ner.items():
            note = " *(Preserved – Policy)*" if label == "DATE" else ""
            st.markdown(f"**{label}** ({len(items)} found){note}:")
            for item in items:
                srcs = ", ".join(get_finding_sources(item))
                st.markdown(f"- `{item}` — *Source: {srcs}*")
    else:
        st.info("No contextual named entities (PERSON, ORG, GPE) detected.")

st.markdown("---")

# ── Source-Document Attribution Breakdown ──────────────────────────────────────
st.subheader("📂 Source-Document Attribution")

if documents:
    # Group findings per source document
    doc_findings_map = {}
    for doc in documents:
        doc_name = doc.metadata.get("source_doc", "Unknown Document")
        if doc_name not in doc_findings_map:
            doc_findings_map[doc_name] = {"regex": [], "ner": [], "chunks": 0}
        doc_findings_map[doc_name]["chunks"] += 1

        for cat, items in active_regex.items():
            for it in items:
                if it in doc.page_content and it not in doc_findings_map[doc_name]["regex"]:
                    doc_findings_map[doc_name]["regex"].append(f"{cat}: {it}")

        for cat, items in active_ner.items():
            for it in items:
                if it in doc.page_content and it not in doc_findings_map[doc_name]["ner"]:
                    doc_findings_map[doc_name]["ner"].append(f"{cat}: {it}")

    for doc_name, data in doc_findings_map.items():
        total_doc_findings = len(data["regex"]) + len(data["ner"])
        badge = "🔴 Sensitive Content" if total_doc_findings > 0 else "🟢 Clean"
        with st.expander(f"📄 {doc_name} — {badge} ({total_doc_findings} items in {data['chunks']} chunk(s))"):
            if total_doc_findings == 0:
                st.success("No sensitive items detected in retrieved chunks from this document.")
            else:
                if data["regex"]:
                    st.markdown("**Regex Findings:**")
                    for f in data["regex"]:
                        st.markdown(f"- `{f}`")
                if data["ner"]:
                    st.markdown("**NER Findings:**")
                    for f in data["ner"]:
                        st.markdown(f"- `{f}`")
else:
    st.info("No document chunks available for attribution analysis.")

# ── Context Transformation Preview ─────────────────────────────────────────────
st.markdown("---")
st.subheader("🔐 Context Transformation Preview")

col_orig, col_safe = st.columns(2)

with col_orig:
    st.markdown("##### Original Retrieved Context")
    st.text_area(
        "Raw Retrieved Text",
        res.get("raw_context", ""),
        height=180,
        disabled=True
    )

with col_safe:
    st.markdown("##### Safe / Sanitized Context")
    if res["action"] == "Blocked":
        st.warning("⚠️ Request Blocked: Context transmission completely suppressed.")
    else:
        st.text_area(
            "Sanitized Text (Sent to LLM)",
            guardrail.get("safe_context", ""),
            height=180,
            disabled=True
        )
