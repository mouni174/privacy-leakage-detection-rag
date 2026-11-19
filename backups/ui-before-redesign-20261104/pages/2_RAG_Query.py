"""
pages/2_RAG_Query.py
---------------------
Feature 1 + Feature 3 – Privacy-aware RAG question answering.

Purpose: Ask questions about uploaded documents.
Includes:
  • Query target selector: All Documents or a specific PDF
  • Privacy policy selector: Redact & Continue or Block Request
  • Question input and Generate Answer button
  • Retrieved context with source metadata
  • Gemini response
  • Clear blocked-request message when applicable

Keeps the existing retrieval and privacy guardrail logic.
Updates session state so the Privacy Dashboard and Audit pages reflect live results.
"""

from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.llm import generate_answer
from src.ner_detector import detect_entities
from src.redactor import redact_sensitive_data

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Query – Privacy RAG",
    page_icon="🔍",
    layout="wide"
)

# ── Session state ──────────────────────────────────────────────────────────────
init_session_state()

# ── Page title & description ───────────────────────────────────────────────────
st.title("🔍 RAG Query")
st.markdown(
    "Ask questions about your uploaded documents. Retrieved context is filtered through "
    "the privacy guardrail before being forwarded to the Gemini LLM."
)

# ── Guard: require indexed documents ───────────────────────────────────────────
if not st.session_state.database_ready or not st.session_state.documents:
    st.warning(
        "⚠️ No documents indexed yet. "
        "Please visit **📄 Document Management** in the sidebar to upload and index PDFs first."
    )
    st.stop()

st.markdown("---")

# ── Sidebar – Query Configuration ──────────────────────────────────────────────
st.sidebar.title("⚙️ Query Configuration")

# 1. Query Target Selector (Feature 3)
scope_options = ["All Documents"] + list(st.session_state.documents.keys())
if st.session_state.selected_scope not in scope_options:
    st.session_state.selected_scope = "All Documents"

selected_scope = st.sidebar.selectbox(
    "Query Target",
    scope_options,
    index=scope_options.index(st.session_state.selected_scope),
    help="Query across all indexed documents or restrict retrieval to a specific document."
)
st.session_state.selected_scope = selected_scope

st.sidebar.markdown("---")

# 2. Privacy Policy Selector (Feature 1)
policy_options = ["Redact & Continue", "Block Request"]
if st.session_state.privacy_policy not in policy_options:
    st.session_state.privacy_policy = "Redact & Continue"

privacy_policy = st.sidebar.radio(
    "🛡️ Privacy Policy",
    policy_options,
    index=policy_options.index(st.session_state.privacy_policy),
    help=(
        "• **Redact & Continue:** Replaces detected PII with placeholder tokens and generates an answer.\n\n"
        "• **Block Request:** Halts processing immediately when PII is detected; zero context is sent to the LLM."
    )
)
st.session_state.privacy_policy = privacy_policy

st.sidebar.markdown("---")
st.sidebar.caption(
    f"📄 {len(st.session_state.documents)} document(s) indexed  |  "
    f"🧩 {sum(d['chunks_count'] for d in st.session_state.documents.values())} chunks"
)

# ── Question input form ────────────────────────────────────────────────────────
st.subheader("❓ Ask a Question")

with st.form("rag_query_form", clear_on_submit=False):
    question = st.text_input(
        "Enter your question",
        placeholder="e.g. What is the employee's salary and contact email?",
        help="Type a question related to your indexed documents."
    )
    submit_button = st.form_submit_button("🔍 Generate Answer", type="primary", use_container_width=True)

# ── Query Execution Pipeline ───────────────────────────────────────────────────
if submit_button:
    if not question.strip():
        st.warning("⚠️ Please enter a question before generating an answer.")
    else:
        try:
            # 1. RAG Retrieval
            with st.spinner("🔎 Retrieving relevant context from ChromaDB…"):
                retrieved = get_relevant_context(
                    question,
                    doc_filter=selected_scope
                )

            if isinstance(retrieved, dict):
                documents = retrieved.get("documents", [])
                context = retrieved.get("context", "")
            else:
                context = retrieved
                documents = []

            # 2. Privacy Guardrail Evaluation
            with st.spinner("🛡️ Inspecting context for privacy leakage…"):
                guardrail = process_context(context, policy=privacy_policy)

            # 3. LLM Answer Generation
            if guardrail.get("blocked", False) or guardrail["action"] == "Blocked":
                answer = None
            else:
                with st.spinner("🤖 Generating answer via Google Gemini…"):
                    answer = generate_answer(guardrail["safe_context"], question)

            # 4. Metrics Computation
            regex_count = sum(len(v) for v in guardrail["regex_findings"].values())
            ner_count = sum(len(v) for v in guardrail["ner_findings"].values())
            total_sensitive = regex_count + ner_count
            action = guardrail["action"]

            if not guardrail["sensitive"] or total_sensitive == 0:
                risk_status = "🟢 Low / Safe"
                risk_desc = "No sensitive information detected in retrieved context."
                risk_badge = "Low / Safe"
            elif action == "Redacted":
                risk_status = "🟡 Moderate / Sanitized"
                risk_desc = "Sensitive information detected and sanitized before LLM transmission."
                risk_badge = "Moderate / Sanitized"
            else:
                risk_status = "🔴 High / Blocked"
                risk_desc = "Sensitive information detected. Transmission blocked by Privacy Policy."
                risk_badge = "High / Blocked"

            # 5. Privacy-safe Audit Record (Feature 5)
            query_ner = detect_entities(question)
            sanitized_query = redact_sensitive_data(question, query_ner)

            cat_counts = []
            for k, v in guardrail["regex_findings"].items():
                if v:
                    cat_counts.append(f"{k.replace('_', ' ').title()} ({len(v)})")
            for k, v in guardrail["ner_findings"].items():
                if v:
                    cat_counts.append(f"{k} ({len(v)})")
            categories_summary = ", ".join(cat_counts) if cat_counts else "None"

            source_docs_list = sorted({
                doc.metadata.get("source_doc", "Document") for doc in documents
            }) if documents else (
                [selected_scope] if selected_scope != "All Documents"
                else ["All Documents"]
            )
            source_docs_str = ", ".join(source_docs_list)

            audit_entry = {
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
            st.session_state.audit_log.append(audit_entry)

            # 6. Save latest query result for Privacy Dashboard persistence (Feature 4)
            st.session_state.last_query_result = {
                "question": question,
                "sanitized_query": sanitized_query,
                "target_scope": selected_scope,
                "privacy_policy": privacy_policy,
                "documents": documents,
                "raw_context": context,
                "guardrail": guardrail,
                "total_sensitive": total_sensitive,
                "regex_count": regex_count,
                "ner_count": ner_count,
                "action": action,
                "risk_status": risk_status,
                "risk_badge": risk_badge,
                "risk_desc": risk_desc,
                "answer": answer,
                "categories_summary": categories_summary,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as exc:
            st.error(f"❌ Error executing query: {exc}")

# ── Render Query Results (Active or Persisted) ─────────────────────────────────
res = st.session_state.get("last_query_result")

if res:
    st.markdown("---")
    st.subheader("📋 Query Results")

    # Policy Action Alert / Blocked Request Message
    if res["action"] == "Blocked":
        st.error(
            "🚫 **Request Blocked:** Sensitive PII was detected in the retrieved context. "
            "LLM answer generation was halted by the Privacy Policy to prevent data leakage."
        )
    elif res["guardrail"].get("sensitive", False):
        st.warning(
            "⚠️ **Sensitive Information Sanitized:** PII was detected and replaced "
            "with redaction tokens prior to LLM submission."
        )
    else:
        st.success(
            "✅ **Request Allowed:** No sensitive information detected in retrieved context."
        )

    # Two-column layout: Context vs LLM Answer
    col_ctx, col_ans = st.columns([1, 1])

    with col_ctx:
        st.markdown("#### 📄 Retrieved Context")
        docs = res.get("documents", [])
        if docs:
            for i, doc in enumerate(docs):
                doc_source = doc.metadata.get("source_doc", "Unknown Source")
                with st.expander(f"Chunk {i + 1} — [{doc_source}]", expanded=(i == 0)):
                    st.write(doc.page_content)
        else:
            st.text_area("Retrieved Context", res.get("raw_context", ""), height=220)

        if res["action"] == "Redacted" and res["guardrail"].get("safe_context"):
            with st.expander("🔐 Sanitized Context (Sent to LLM)", expanded=False):
                st.text_area("Sanitized Content", res["guardrail"]["safe_context"], height=180, disabled=True)

    with col_ans:
        st.markdown("#### 🤖 Gemini Response")
        if res["action"] == "Blocked":
            st.info(
                "🔒 **No answer generated.** The request was blocked to protect confidential data."
            )
        elif res.get("answer"):
            st.success(res["answer"])
        else:
            st.info("No response returned from the model.")

    st.markdown("---")
    st.info(
        "🛡️ **Detailed Privacy Telemetry:** Open **Privacy Dashboard** in the sidebar "
        "to inspect the entity breakdown, regex findings, and source attribution for this query."
    )
