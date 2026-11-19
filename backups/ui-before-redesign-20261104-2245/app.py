"""Home dashboard for Privacy Leakage Detection in RAG Systems."""

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.ui import apply_global_styles, render_section_heading, render_sidebar_brand

load_dotenv()

st.set_page_config(
    page_title="Privacy RAG | Security overview",
    page_icon="🛡️",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

documents = st.session_state.documents
audit_log = st.session_state.audit_log
total_docs = len(documents)
total_chunks = sum(document["chunks_count"] for document in documents.values())
total_queries = len(audit_log)
total_blocked = sum(
    1 for entry in audit_log if entry.get("Guardrail Action") == "Blocked"
)
database_ready = st.session_state.database_ready

status_state = "ready" if database_ready else "empty"
status_label = "Knowledge base active" if database_ready else "Awaiting documents"

st.markdown(
    f"""
    <section class="pld-hero">
        <div class="pld-hero-kicker">Privacy Leakage Detection in RAG Systems</div>
        <h1 class="pld-hero-title">Privacy-first answers.<br>Confidence at every step.</h1>
        <p class="pld-hero-copy">
            Inspect retrieved context before it reaches a language model. Detect sensitive
            information, enforce your privacy policy, and keep a privacy-safe audit trail.
        </p>
        <div class="pld-hero-meta">
            <span class="pld-status-chip" data-state="{status_state}">
                <span class="pld-status-dot"></span>{status_label}
            </span>
            <span class="pld-meta-chip">Regex + spaCy NER</span>
            <span class="pld-meta-chip">Gemini protected by guardrails</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.space("medium")

with st.container(horizontal=True):
    st.metric(":material/folder_open: Documents indexed", total_docs, border=True)
    st.metric(":material/data_object: Text chunks", total_chunks, border=True)
    st.metric(":material/search: Queries processed", total_queries, border=True)
    st.metric(":material/block: Requests blocked", total_blocked, border=True)

st.space("small")
render_section_heading("Quick actions", "Continue where you left off.")
action_columns = st.columns(4)
with action_columns[0]:
    st.page_link(
        "pages/1_Document_Management.py",
        label="Manage documents",
        icon=":material/upload_file:",
        width="stretch",
    )
with action_columns[1]:
    st.page_link(
        "pages/2_RAG_Query.py",
        label="Run a privacy-aware query",
        icon=":material/manage_search:",
        width="stretch",
    )
with action_columns[2]:
    st.page_link(
        "pages/3_Privacy_Dashboard.py",
        label="View privacy dashboard",
        icon=":material/shield:",
        width="stretch",
    )
with action_columns[3]:
    st.page_link(
        "pages/4_Privacy_Audit.py",
        label="Review audit trail",
        icon=":material/receipt_long:",
        width="stretch",
    )

st.space("small")
render_section_heading(
    "How the protection pipeline works",
    "A zero-trust inspection layer between semantic retrieval and answer generation.",
)

workflow = [
    (
        "01",
        ":material/description:",
        "Ingest and index",
        "Upload PDFs, split their text recursively, and index document chunks in ChromaDB.",
    ),
    (
        "02",
        ":material/travel_explore:",
        "Retrieve relevant context",
        "Sentence Transformer embeddings power semantic search, with optional document scope.",
    ),
    (
        "03",
        ":material/policy:",
        "Inspect and enforce",
        "Regex patterns and spaCy NER detect sensitive content; block or redact by policy.",
    ),
    (
        "04",
        ":material/verified_user:",
        "Generate and audit",
        "Gemini receives guardrail-approved context; privacy-safe results feed the audit trail.",
    ),
]

workflow_columns = st.columns(4)
for column, (number, icon, title, description) in zip(workflow_columns, workflow):
    with column:
        with st.container(border=True):
            st.markdown(f'<div class="pld-step-number">STEP {number}</div>', unsafe_allow_html=True)
            st.markdown(f"### {icon} {title}")
            st.caption(description)

st.space("small")
render_section_heading(
    "Privacy protection",
    "Detection, policy enforcement, and reporting use the application's existing processing pipeline.",
)

protection_columns = st.columns(2)
with protection_columns[0]:
    with st.container(border=True):
        st.markdown(":material/radar:  **Detection coverage**")
        st.markdown(
            """
            <div class="pld-feature-label">Structured identifiers</div>
            Email, phone, PAN, Aadhaar, bank-account, IFSC, card, and government-ID patterns.

            <div class="pld-feature-label">Contextual entities</div>
            spaCy NER identifies person, organization, location, date, and money entities.
            """,
            unsafe_allow_html=True,
        )
with protection_columns[1]:
    with st.container(border=True):
        st.markdown(":material/gpp_good:  **Policy and governance**")
        st.markdown(
            """
            <div class="pld-feature-label">Choose the response</div>
            Redact and continue with sanitized context, or block the request when sensitive
            content is detected.

            <div class="pld-feature-label">Keep a privacy-safe record</div>
            Review detection counts and sanitized queries, export audit logs, and download
            permanently redacted PDF copies.
            """,
            unsafe_allow_html=True,
        )

st.space("small")
render_section_heading(
    "Recent activity",
    "Latest query events from this session. Query text is shown only in its logged, sanitized form.",
)

if audit_log:
    recent_activity = [
        {
            "Timestamp": entry.get("Timestamp", ""),
            "Sanitized query": entry.get("Sanitized Query", ""),
            "Target": entry.get("Target Scope", ""),
            "Action": entry.get("Guardrail Action", ""),
            "Risk": entry.get("Risk Status", ""),
        }
        for entry in reversed(audit_log[-5:])
    ]
    st.dataframe(
        recent_activity,
        hide_index=True,
        width="stretch",
        column_config={
            "Timestamp": st.column_config.TextColumn("Time", width="medium"),
            "Sanitized query": st.column_config.TextColumn(
                "Sanitized query", width="large"
            ),
            "Target": st.column_config.TextColumn("Scope", width="medium"),
            "Action": st.column_config.TextColumn("Guardrail action", width="small"),
            "Risk": st.column_config.TextColumn("Risk", width="medium"),
        },
    )
else:
    st.info(
        "No query activity in this session yet. Open **Run a privacy-aware query** "
        "after indexing a document to see real activity here."
    )

if not database_ready:
    st.info(
        "Start by adding a PDF to the knowledge base. Your document processing, "
        "privacy detection, and sanitized export controls are available in Document Management."
    )

st.caption(
    "Privacy Leakage Detection in RAG Systems · Session-scoped metrics and audit activity"
)
