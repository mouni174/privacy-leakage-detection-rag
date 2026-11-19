"""
app.py – Home / Overview
------------------------
Entry point for the Privacy Leakage Detection in RAG Systems application.

Purpose: Project overview only.
Displays:
  • Project title and description
  • System architecture / workflow
  • Feature overview
  • Session statistics: indexed documents, total chunks, queries processed, blocked requests
  • Instructions for getting started

No document upload forms, query inputs, detailed detection results, or audit tables live here.
"""

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state

load_dotenv()

# ── Page config (entry-point only) ─────────────────────────────────────────────
st.set_page_config(
    page_title="Home – Privacy Leakage Detection in RAG",
    page_icon="🏠",
    layout="wide"
)

# ── Session state ──────────────────────────────────────────────────────────────
init_session_state()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🔒 Privacy Leakage Detection in RAG Systems")
st.markdown(
    """
    An enterprise-grade research prototype that prevents, redacts, and audits **Personally Identifiable
    Information (PII)** leakage in Retrieval-Augmented Generation (RAG) pipelines *before*
    retrieved content reaches the Large Language Model.
    """
)

st.markdown("---")

# ── Live session statistics ────────────────────────────────────────────────────
st.subheader("📊 Session Statistics")

total_docs = len(st.session_state.documents)
total_chunks = sum(
    d["chunks_count"] for d in st.session_state.documents.values()
)
total_queries = len(st.session_state.audit_log)
total_blocked = sum(
    1 for a in st.session_state.audit_log
    if a.get("Guardrail Action") == "Blocked"
)

s_col1, s_col2, s_col3, s_col4 = st.columns(4)
s_col1.metric("📄 Documents Indexed", total_docs)
s_col2.metric("🧩 Total Chunks", total_chunks)
s_col3.metric("💬 Queries Processed", total_queries)
s_col4.metric("🚫 Requests Blocked", total_blocked)

st.markdown("---")

# ── System Architecture & Workflow ─────────────────────────────────────────────
st.subheader("🏗️ System Architecture & Workflow")

st.markdown(
    """
    The system sits as a zero-trust inspection layer between the retrieval engine and the generative model:
    """
)

# Visual Workflow Pipeline
arch_col1, arch_col2, arch_col3, arch_col4 = st.columns(4)

with arch_col1:
    st.markdown(
        """
        ##### 1. Ingestion & Indexing
        - Multi-PDF upload
        - Recursive chunking with `source_doc` metadata
        - High-dimensional vector indexing in ChromaDB
        """
    )

with arch_col2:
    st.markdown(
        """
        ##### 2. Scope & Retrieval
        - Scope queries to *All Documents* or an isolated document
        - Semantic similarity retrieval ($k=3$)
        - Source document attribution mapping
        """
    )

with arch_col3:
    st.markdown(
        """
        ##### 3. Privacy Guardrail
        - **Dual Detection**:
          - Regex patterns (SSN, PAN, Email, Phone, Cards)
          - spaCy NER (Person, Org, Location)
        - **Policy Enforcement**:
          - *Block Request* (Zero LLM leakage)
          - *Redact & Continue* (Token sanitization)
        """
    )

with arch_col4:
    st.markdown(
        """
        ##### 4. Generation & Audit
        - Gemini inference strictly on sanitized context
        - Live telemetry on Privacy Dashboard
        - Session audit log with zero raw PII stored
        - True byte-level PDF redaction with PyMuPDF
        """
    )

st.markdown("---")

# ── Feature Overview ───────────────────────────────────────────────────────────
st.subheader("🗂️ Feature Overview")

feat_col1, feat_col2 = st.columns(2)

with feat_col1:
    st.markdown(
        """
        #### 📄 Document Management (`pages/1_Document_Management.py`)
        - **Batch Ingestion**: Upload multiple PDF documents across sessions.
        - **Chunk & Metadata Tracking**: Monitor chunk counts and collection status per file.
        - **Permanent PDF Redaction**: Download sanitized PDFs with black-box visual redaction via PyMuPDF.

        #### 🔍 RAG Query (`pages/2_RAG_Query.py`)
        - **Target Scoping**: Run cross-document queries or isolate a single confidential PDF.
        - **Configurable Privacy Policy**: Choose between *Redact & Continue* or *Block Request*.
        - **Secure Generation**: Prompt Google Gemini using sanitized context only.
        """
    )

with feat_col2:
    st.markdown(
        """
        #### 🛡️ Privacy Dashboard (`pages/3_Privacy_Dashboard.py`)
        - **Real-Time Telemetry**: Sensitive item counts, regex findings, and NER detections.
        - **Risk Classification**: Transparent rule-based risk ratings (Low, Moderate, High).
        - **Structured Detection Report**: Category breakdown and source document attribution for the latest query.

        #### 📜 Privacy Audit (`pages/4_Privacy_Audit.py`)
        - **Zero Raw PII Storage**: Records only finding counts, categories, and redacted queries.
        - **Compliance Auditing**: Review actions, timestamps, policy rules, and LLM invocation state.
        - **CSV Export**: Download audit logs for governance and security review.
        """
    )

st.markdown("---")

# ── Instructions for Getting Started ───────────────────────────────────────────
st.subheader("🚀 Getting Started")

step_col1, step_col2, step_col3 = st.columns(3)

with step_col1:
    st.markdown(
        """
        **Step 1: Upload Documents**  
        Navigate to **📄 Document Management** in the sidebar. Upload your PDF files. Each file is chunked, indexed into ChromaDB, and sanitized for download.
        """
    )

with step_col2:
    st.markdown(
        """
        **Step 2: Ask Questions**  
        Navigate to **🔍 RAG Query**. Select your target document and privacy policy (*Redact & Continue* or *Block Request*), then generate answers.
        """
    )

with step_col3:
    st.markdown(
        """
        **Step 3: Monitor & Audit**  
        Visit **🛡️ Privacy Dashboard** to inspect detected entities for the latest query, and **📜 Privacy Audit** to review or export session event logs.
        """
    )

st.markdown("")

if not st.session_state.database_ready:
    st.info(
        "👈 **Ready to start?** Open **Document Management** from the sidebar to upload your first PDF."
    )
else:
    st.success(
        f"✅ **System Ready.** {total_docs} document(s) and {total_chunks} chunk(s) indexed. "
        "Proceed to **RAG Query** in the sidebar to ask questions."
    )

st.markdown("---")
st.caption(
    "Research Prototype — Privacy Leakage Detection in RAG Systems | "
    "Dual-Layer Detection: Regex + spaCy NER | "
    "Engineered for Zero-Trust AI Workflows"
)