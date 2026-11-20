"""Privacy-aware document query interface."""

from datetime import datetime
from time import perf_counter

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.llm import (
    GeminiGenerationError,
    generate_answer,
    has_usable_context,
)
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
    page_title="RAG Query | Privacy Leakage Detection",
    page_icon=":material/forum:",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

documents_in_session = st.session_state.documents
total_chunks = sum(
    document["chunks_count"] for document in documents_in_session.values()
)

render_page_header(
    title="Secure RAG Query",
    description=(
        "Search indexed sources and inspect retrieved context before model generation. "
        "Your selected privacy policy governs whether sensitive context is sanitized "
        "or the request is stopped."
    ),
    eyebrow="02 / Guarded retrieval",
    icon="forum",
    status_label="Retrieval ready" if st.session_state.database_ready else "Index required",
)

if not st.session_state.database_ready or not documents_in_session:
    render_empty_state(
        eyebrow="QUERY STATION",
        title="No documents indexed yet",
        description=(
            "The guarded query console needs an indexed PDF before it can retrieve "
            "anything. No sample documents or results are shown."
        ),
        icon="database",
        steps=(
            "Upload a PDF in Document Management.",
            "Wait for indexing and sanitized-copy processing to finish.",
            "Return here to choose a scope, set a policy, and ask.",
        ),
        actions=(
            (
                "pages/1_Document_Management.py",
                "Open Document Management",
                "folder_managed",
            ),
        ),
    )
    st.stop()

document_ids = [
    info["document_id"]
    for info in documents_in_session.values()
    if info.get("document_id")
]
indexed_document_ids = document_ids
scope_options = ["All Documents", *document_ids]
legacy_documents = [
    info
    for info in documents_in_session.values()
    if not info.get("document_id")
]
if st.session_state.get("query_scope_selector") not in scope_options:
    st.session_state.pop("query_scope_selector", None)
if st.session_state.selected_document_id not in document_ids:
    st.session_state.selected_document_id = None
if st.session_state.selected_scope not in scope_options:
    st.session_state.selected_scope = "All Documents"
if st.session_state.selected_scope == "All Documents":
    st.session_state.selected_document_id = None
else:
    st.session_state.selected_document_id = st.session_state.selected_scope

if legacy_documents:
    st.warning(
        f"{len(legacy_documents)} legacy document(s) have no stable document ID and "
        "are excluded from retrieval to prevent filename collisions. Re-upload them "
        "to index them with isolated IDs."
    )

policy_options = ["Redact & Continue", "Block Request"]
if st.session_state.privacy_policy not in policy_options:
    st.session_state.privacy_policy = "Redact & Continue"

render_section_heading(
    "Query console",
    "Set the search boundary and privacy response, then ask a question grounded in your indexed PDFs.",
)

controls_column, conversation_column = st.columns([0.88, 1.65], gap="large")
with controls_column:
    with st.container(border=True):
        st.markdown('<div class="pld-story-index">01 / SCOPE</div>', unsafe_allow_html=True)
        st.markdown("### Retrieval controls")
        st.caption(
            f"{len(documents_in_session)} indexed source(s) · "
            f"{total_chunks} searchable chunks"
        )
        st.markdown("**:material/folder_open: Document scope**")
        selected_scope = st.selectbox(
            "Search across",
            scope_options,
            index=scope_options.index(st.session_state.selected_scope),
            key="query_scope_selector",
            format_func=lambda value: (
                "All Documents"
                if value == "All Documents"
                else sanitize_sensitive_text(
                    documents_in_session.get(value, {}).get("original_filename", value)
                )
            ),
            help="Search all indexed documents or limit retrieval to one source.",
        )
        if selected_scope not in scope_options:
            st.error("The selected document is not part of this session's registry.")
            st.stop()
        st.session_state.selected_scope = selected_scope
        st.session_state.selected_document_id = (
            None if selected_scope == "All Documents" else selected_scope
        )

        st.markdown('<div class="pld-story-index">02 / POLICY</div>', unsafe_allow_html=True)
        st.markdown("**:material/policy: Privacy response**")
        privacy_policy = st.radio(
            "When sensitive data is detected",
            policy_options,
            index=policy_options.index(st.session_state.privacy_policy),
            key="query_privacy_policy_selector",
            help=(
                "Redact & Continue sanitizes the question and retrieved context before "
                "model transmission. Block Request stops generation if confirmed "
                "sensitive data is found."
            ),
        )
        st.session_state.privacy_policy = privacy_policy

        policy_note = (
            "The question and retrieved context are sanitized before Gemini receives them."
            if privacy_policy == "Redact & Continue"
            else "Generation is halted when confirmed sensitive data is detected."
        )
        st.caption(f":material/verified_user:  {policy_note}")

with conversation_column:
    with st.container(border=True):
        st.markdown('<div class="pld-story-index">03 / ASK</div>', unsafe_allow_html=True)
        st.markdown("### Start a private conversation")
        st.caption(
            "Retrieved source text is kept out of the visible interface. The model "
            "receives only the question and context approved by the active privacy guardrail."
        )
        with st.form("rag_query_form", clear_on_submit=False):
            question = st.text_input(
                "Your question",
                placeholder="Ask a question about your indexed PDFs…",
                help="Ask about content in your indexed documents.",
            )
            submit_button = st.form_submit_button(
                "Inspect context and generate answer",
                type="primary",
                width="stretch",
            )

if submit_button:
    if not question.strip():
        st.warning("Enter a question before generating an answer.")
    else:
        request_started = perf_counter()
        try:
            with st.spinner("Retrieving relevant context from ChromaDB…"):
                retrieved = get_relevant_context(
                    question,
                    document_ids=(
                        indexed_document_ids
                        if selected_scope == "All Documents"
                        else None
                    ),
                    document_id=(
                        selected_scope
                        if selected_scope != "All Documents"
                        and documents_in_session.get(selected_scope, {}).get("document_id")
                        else None
                    ),
                    doc_filter=(
                        documents_in_session.get(selected_scope, {}).get(
                            "original_filename", selected_scope
                        )
                        if selected_scope != "All Documents"
                        and not documents_in_session.get(selected_scope, {}).get("document_id")
                        else None
                    ),
                )

            if isinstance(retrieved, dict):
                retrieved_documents = retrieved.get("documents", [])
                context = retrieved.get("context", "")
            else:
                context = retrieved
                retrieved_documents = []

            with st.spinner("Inspecting context for privacy leakage…"):
                guardrail = process_context(
                    context,
                    policy=privacy_policy,
                    query=question,
                )

            generation_error = None
            if guardrail.get("blocked", False) or guardrail["action"] == "Blocked":
                answer = None
            else:
                try:
                    with st.spinner("Generating an evidence-grounded answer via Gemini…"):
                        answer = generate_answer(
                            guardrail["safe_context"] or "",
                            guardrail["safe_query"] or "",
                        )
                    answer = sanitize_sensitive_text(answer)
                except GeminiGenerationError as exc:
                    answer = None
                    generation_error = str(exc)

            regex_count = sum(
                finding.source == "Regex"
                and finding.classification == "sensitive"
                for finding in guardrail["findings"]
            )
            ner_count = sum(
                finding.source == "NER"
                and finding.classification == "sensitive"
                for finding in guardrail["findings"]
            )
            total_sensitive = regex_count + ner_count
            action = guardrail["action"]

            if not guardrail["sensitive"] or total_sensitive == 0:
                risk_status = "🟢 Low / Safe"
                risk_desc = "No confirmed sensitive information detected in the question or retrieved context."
                risk_badge = "Low / Safe"
            elif action == "Redacted":
                risk_status = "🟡 Moderate / Sanitized"
                risk_desc = "Confirmed sensitive information in the question or context was sanitized before model transmission."
                risk_badge = "Moderate / Sanitized"
            else:
                risk_status = "🔴 High / Blocked"
                risk_desc = "Confirmed sensitive information detected. Transmission was blocked by the selected policy."
                risk_badge = "High / Blocked"

            sanitized_query = sanitize_sensitive_text(question)

            category_counts = {}
            for finding in guardrail["findings"]:
                if finding.classification == "sensitive":
                    category_counts[finding.category] = (
                        category_counts.get(finding.category, 0) + 1
                    )
            cat_counts = [
                f"{category.replace('_', ' ').title()} ({count})"
                for category, count in sorted(category_counts.items())
            ]
            categories_summary = ", ".join(cat_counts) if cat_counts else "None"

            source_docs_list = sorted(
                {
                    sanitize_sensitive_text(
                        document.metadata.get("source_doc", "Document")
                    )
                    for document in retrieved_documents
                }
            ) if retrieved_documents else (
                [sanitize_sensitive_text(selected_scope)]
                if selected_scope != "All Documents"
                else ["All Documents"]
            )
            source_docs_str = ", ".join(source_docs_list)
            safe_target_scope = (
                sanitize_sensitive_text(
                    documents_in_session.get(selected_scope, {}).get(
                        "original_filename", selected_scope
                    )
                )
                if selected_scope != "All Documents"
                else "All Documents"
            )

            source_findings = {}
            for document in retrieved_documents:
                source_name = sanitize_sensitive_text(
                    document.metadata.get("source_doc", "Unknown document")
                )
                entry = source_findings.setdefault(
                    source_name,
                    {
                        "chunks": 0,
                        "regex": set(),
                        "ner": set(),
                    },
                )
                entry["chunks"] += 1

                for finding in guardrail["findings"]:
                    if (
                        finding.location == "context"
                        and finding.classification == "sensitive"
                        and finding.matched_text in document.page_content
                    ):
                        detector = "regex" if finding.source == "Regex" else "ner"
                        entry[detector].add(
                            (finding.category, finding.start, finding.end)
                        )

            source_attribution = []
            for source_name, findings in source_findings.items():
                source_regex_count = len(findings["regex"])
                source_ner_count = len(findings["ner"])
                source_total = source_regex_count + source_ner_count
                source_attribution.append(
                    {
                        "Source document": source_name,
                        "Retrieved chunks": findings["chunks"],
                        "Regex findings": source_regex_count,
                        "NER findings": source_ner_count,
                        "Assessment": (
                            "Findings detected" if source_total else "No findings"
                        ),
                    }
                )

            source_metadata = [
                {
                    "Source": sanitize_sensitive_text(
                        document.metadata.get("source_doc", "Document")
                    ),
                    "Page": document.metadata.get("page", "—"),
                    "Passage": f"Retrieved chunk {index}",
                }
                for index, document in enumerate(retrieved_documents, start=1)
            ]

            query_latency_ms = round((perf_counter() - request_started) * 1000, 3)
            redacted_entity_count = sum(
                finding.redaction_status == "redacted"
                for finding in guardrail["findings"]
            )

            audit_entry = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Sanitized Query": sanitized_query,
                "Target Scope": safe_target_scope,
                "Retrieved Chunk Count": len(retrieved_documents) if retrieved_documents else 0,
                "Source Documents": source_docs_str,
                "Regex Finding Count": regex_count,
                "NER Finding Count": ner_count,
                "Total Sensitive Items": total_sensitive,
                "Redacted Entity Count": redacted_entity_count,
                "Query Processing Latency (ms)": query_latency_ms,
                "Detected Categories": categories_summary,
                "Privacy Policy": privacy_policy,
                "Guardrail Action": guardrail["action"],
                "Policy Rationale": guardrail["rationale"],
                "Risk Status": risk_badge,
                "LLM Invoked": (
                    "No (Blocked)"
                    if guardrail["action"] == "Blocked"
                    else "Yes"
                    if has_usable_context(guardrail["safe_context"])
                    else "No (Insufficient evidence)"
                ),
                "Generation Status": (
                    "Unavailable"
                    if generation_error
                    else "Not invoked"
                    if guardrail["action"] == "Blocked"
                    or not has_usable_context(guardrail["safe_context"])
                    else "Completed"
                ),
            }
            st.session_state.audit_log.append(audit_entry)

            st.session_state.last_query_result = {
                "sanitized_query": sanitized_query,
                "target_scope": safe_target_scope,
                "target_document_id": (
                    selected_scope if selected_scope != "All Documents" else None
                ),
                "privacy_policy": privacy_policy,
                "sources": source_metadata,
                "source_attribution": source_attribution,
                "guardrail": {
                    "sensitive": guardrail["sensitive"],
                    "regex_findings": {
                        category: len(values)
                        for category, values in guardrail["regex_findings"].items()
                    },
                    "ner_findings": {
                        category: len(values)
                        for category, values in guardrail["ner_findings"].items()
                    },
                },
                "total_sensitive": total_sensitive,
                "redacted_count": redacted_entity_count,
                "regex_count": regex_count,
                "ner_count": ner_count,
                "latency_ms": query_latency_ms,
                "action": action,
                "risk_status": risk_status,
                "risk_badge": risk_badge,
                "risk_desc": risk_desc,
                "answer": answer,
                "generation_error": generation_error,
                "categories_summary": categories_summary,
                "policy_rationale": guardrail["rationale"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as exc:
            st.error(
                "Query could not be completed "
                f"({type(exc).__name__}). Check the index and retry."
            )

result = st.session_state.get("last_query_result")
if result:
    st.space("small")
    render_section_heading(
        "Conversation result",
        f"{result['target_scope']} · evaluated {result['timestamp']}",
    )

    with st.container(border=True):
        if result["action"] == "Blocked":
            st.error(
                "Request blocked. Confirmed sensitive information was detected and no answer "
                "was generated or sent to Gemini."
            )
        elif result["guardrail"].get("sensitive", False):
            st.warning(
                "Confirmed sensitive information was redacted from the question or "
                "context before either was sent to Gemini."
            )
        else:
            st.success(
                "No confirmed sensitive information was detected in the question or "
                "retrieved context."
            )

        st.chat_message("user", avatar="👤").markdown(
            result.get("sanitized_query", "[Query unavailable]")
        )

        response_message = st.chat_message("assistant", avatar="🛡️")
        if result["action"] == "Blocked":
            response_message.info(
                "Generation was stopped by the active privacy policy."
            )
        elif result.get("answer"):
            response_message.markdown(result["answer"])
        elif result.get("generation_error"):
            response_message.warning(result["generation_error"])
        else:
            response_message.info(
                "No answer was generated. The retrieved documents did not contain "
                "sufficient evidence or generation was stopped by policy."
            )

    st.space("small")
    result_columns = st.columns([1, 1.35], gap="large")
    with result_columns[0]:
        with st.container(border=True):
            st.markdown("### :material/source: Retrieved sources")
            source_rows = result.get("sources", [])
            if source_rows:
                st.dataframe(
                    source_rows,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Source": st.column_config.TextColumn(
                            "Document", width="large"
                        ),
                        "Page": st.column_config.TextColumn("Page", width="small"),
                        "Passage": st.column_config.TextColumn("Passage", width="medium"),
                    },
                )
            else:
                st.info("No source metadata was returned for this retrieval.")

    with result_columns[1]:
        with st.container(border=True):
            st.markdown("### :material/verified_user: Privacy inspection")
            st.markdown(
                f"**Guardrail action:** {result['action']}  \n"
                f"**Risk:** {result['risk_badge']}  \n"
                f"**Sensitive items:** {result['total_sensitive']}  \n"
                f"**Detected categories:** {result['categories_summary']}"
            )

            st.info(
                "Retrieved text is not displayed in the interface. "
                "The active policy controls whether approved context is sent to Gemini."
            )

    st.page_link(
        "pages/3_Privacy_Dashboard.py",
        label="Open detailed privacy dashboard",
        width="content",
    )
else:
    with st.container(border=True):
        st.markdown("### :material/chat_bubble_outline: Your conversation will appear here")
        st.caption(
            "Submit a question to see the sanitized prompt, generated answer, retrieved "
            "source metadata, and the guardrail's actual decision."
        )
