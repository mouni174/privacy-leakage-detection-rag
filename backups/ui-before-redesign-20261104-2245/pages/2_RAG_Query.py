"""Privacy-aware document query interface."""

from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.retriever import get_relevant_context
from src.guardrail import process_context
from src.llm import generate_answer
from src.ner_detector import detect_entities
from src.redactor import redact_sensitive_data
from src.ui import apply_global_styles, render_section_heading, render_sidebar_brand

load_dotenv()

st.set_page_config(
    page_title="RAG Query | Privacy RAG",
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

st.markdown(
    f"""
    <section class="pld-hero">
        <div class="pld-hero-kicker">Private retrieval · policy-enforced generation</div>
        <h1 class="pld-hero-title">Ask your knowledge base</h1>
        <p class="pld-hero-copy">
            Retrieve relevant passages from your PDFs, inspect them with the privacy
            guardrail, and send only approved context to Gemini.
        </p>
        <div class="pld-hero-meta">
            <span class="pld-status-chip" data-state="{'ready' if st.session_state.database_ready else 'empty'}">
                <span class="pld-status-dot"></span>
                {"Retrieval ready" if st.session_state.database_ready else "Index required"}
            </span>
            <span class="pld-meta-chip">{len(documents_in_session)} indexed source{"s" if len(documents_in_session) != 1 else ""}</span>
            <span class="pld-meta-chip">{total_chunks} searchable chunks</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.space("medium")

if not st.session_state.database_ready or not documents_in_session:
    with st.container(border=True):
        st.markdown("### :material/database: Your private index is not ready yet")
        st.write(
            "Index a PDF before starting a conversation. Once documents are processed, "
            "you can scope retrieval and choose how the privacy guardrail handles findings."
        )
        st.page_link(
            "pages/1_Document_Management.py",
            label="Manage documents",
            width="content",
        )
    st.stop()

scope_options = ["All Documents"] + list(documents_in_session.keys())
if st.session_state.selected_scope not in scope_options:
    st.session_state.selected_scope = "All Documents"

policy_options = ["Redact & Continue", "Block Request"]
if st.session_state.privacy_policy not in policy_options:
    st.session_state.privacy_policy = "Redact & Continue"

render_section_heading(
    "Conversation controls",
    "Choose the retrieval scope and the guardrail action for sensitive findings.",
)

with st.container(border=True):
    control_columns = st.columns([1.05, 1.7], vertical_alignment="center")
    with control_columns[0]:
        st.markdown("**:material/folder_open: Document scope**")
        selected_scope = st.selectbox(
            "Search across",
            scope_options,
            index=scope_options.index(st.session_state.selected_scope),
            key="query_scope_selector",
            help="Search all indexed documents or limit retrieval to one source.",
        )
        st.session_state.selected_scope = selected_scope

    with control_columns[1]:
        st.markdown("**:material/policy: Privacy policy**")
        privacy_policy = st.radio(
            "When sensitive data is detected",
            policy_options,
            index=policy_options.index(st.session_state.privacy_policy),
            horizontal=True,
            key="query_privacy_policy_selector",
            help=(
                "Redact & Continue sanitizes retrieved context before model transmission. "
                "Block Request stops generation if sensitive data is found."
            ),
        )
        st.session_state.privacy_policy = privacy_policy

    policy_note = (
        "Detected context is sanitized before Gemini receives it."
        if privacy_policy == "Redact & Continue"
        else "Generation is halted when sensitive context is detected."
    )
    st.caption(f":material/verified_user:  {policy_note}")

st.space("small")
render_section_heading(
    "Secure conversation",
    "Questions are answered using retrieved document context and the selected privacy policy.",
)

with st.container(border=True):
    st.markdown("### :material/forum: Ask a question")
    st.caption(
        "Use document-grounded questions. Retrieved source text is kept out of the "
        "visible interface; the model receives only context approved by the guardrail."
    )
    with st.form("rag_query_form", clear_on_submit=False):
        question = st.text_input(
            "Your question",
            placeholder="Ask a question about your indexed PDFs…",
            help="Ask about content in your indexed documents.",
        )
        submit_button = st.form_submit_button(
            "Generate answer",
            type="primary",
            width="stretch",
        )

if submit_button:
    if not question.strip():
        st.warning("Enter a question before generating an answer.")
    else:
        try:
            with st.spinner("Retrieving relevant context from ChromaDB…"):
                retrieved = get_relevant_context(
                    question,
                    doc_filter=selected_scope,
                )

            if isinstance(retrieved, dict):
                retrieved_documents = retrieved.get("documents", [])
                context = retrieved.get("context", "")
            else:
                context = retrieved
                retrieved_documents = []

            with st.spinner("Inspecting context for privacy leakage…"):
                guardrail = process_context(context, policy=privacy_policy)

            if guardrail.get("blocked", False) or guardrail["action"] == "Blocked":
                answer = None
            else:
                with st.spinner("Generating answer via Google Gemini…"):
                    answer = generate_answer(guardrail["safe_context"], question)

            regex_count = sum(len(values) for values in guardrail["regex_findings"].values())
            ner_count = sum(len(values) for values in guardrail["ner_findings"].values())
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

            query_ner = detect_entities(question)
            sanitized_query = redact_sensitive_data(question, query_ner)

            cat_counts = []
            for category, values in guardrail["regex_findings"].items():
                if values:
                    cat_counts.append(f"{category.replace('_', ' ').title()} ({len(values)})")
            for category, values in guardrail["ner_findings"].items():
                if values:
                    cat_counts.append(f"{category} ({len(values)})")
            categories_summary = ", ".join(cat_counts) if cat_counts else "None"

            source_docs_list = sorted(
                {
                    document.metadata.get("source_doc", "Document")
                    for document in retrieved_documents
                }
            ) if retrieved_documents else (
                [selected_scope] if selected_scope != "All Documents"
                else ["All Documents"]
            )
            source_docs_str = ", ".join(source_docs_list)

            audit_entry = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Sanitized Query": sanitized_query,
                "Target Scope": selected_scope,
                "Retrieved Chunk Count": len(retrieved_documents) if retrieved_documents else 0,
                "Source Documents": source_docs_str,
                "Regex Finding Count": regex_count,
                "NER Finding Count": ner_count,
                "Total Sensitive Items": total_sensitive,
                "Detected Categories": categories_summary,
                "Privacy Policy": privacy_policy,
                "Guardrail Action": guardrail["action"],
                "Risk Status": risk_badge,
                "LLM Invoked": "No (Blocked)" if guardrail["action"] == "Blocked" else "Yes",
            }
            st.session_state.audit_log.append(audit_entry)

            st.session_state.last_query_result = {
                "question": question,
                "sanitized_query": sanitized_query,
                "target_scope": selected_scope,
                "privacy_policy": privacy_policy,
                "documents": retrieved_documents,
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
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        except Exception as exc:
            st.error(f"Error executing query: {exc}")

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
                "Request blocked. Sensitive information was detected and no answer "
                "was generated or sent to Gemini."
            )
        elif result["guardrail"].get("sensitive", False):
            st.warning(
                "Sensitive information was detected and redacted before context "
                "was sent to Gemini."
            )
        else:
            st.success("No sensitive information was detected in retrieved context.")

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
        else:
            response_message.info("No response was returned from the model.")

    st.space("small")
    result_columns = st.columns([1, 1.35], gap="large")
    with result_columns[0]:
        with st.container(border=True):
            st.markdown("### :material/source: Retrieved sources")
            result_documents = result.get("documents", [])
            if result_documents:
                source_rows = []
                for index, document in enumerate(result_documents, start=1):
                    metadata = document.metadata
                    source_rows.append(
                        {
                            "Source": metadata.get("source_doc", "Document"),
                            "Page": metadata.get("page", "—"),
                            "Passage": f"Retrieved chunk {index}",
                        }
                    )
                st.dataframe(
                    source_rows,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Source": st.column_config.TextColumn("Document", width="large"),
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
