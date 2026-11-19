"""PDF upload, vector indexing, and sanitized document exports."""

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store, add_documents_to_vector_store
from src.pdf_sanitizer import sanitize_pdf
from src.ui import apply_global_styles, render_section_heading, render_sidebar_brand

load_dotenv()

st.set_page_config(
    page_title="Document Management | Privacy RAG",
    page_icon=":material/folder_managed:",
    layout="wide",
)

init_session_state()
apply_global_styles()
render_sidebar_brand()
st.sidebar.caption("Privacy-first RAG monitoring")

documents = st.session_state.documents
total_docs = len(documents)
total_chunks = sum(document["chunks_count"] for document in documents.values())

st.markdown(
    f"""
    <section class="pld-hero">
        <div class="pld-hero-kicker">Knowledge base · secure ingestion</div>
        <h1 class="pld-hero-title">Document workspace</h1>
        <p class="pld-hero-copy">
            Add PDF sources to your private knowledge base. Each upload is split,
            embedded, indexed for semantic retrieval, and prepared as a permanently
            sanitized copy for download.
        </p>
        <div class="pld-hero-meta">
            <span class="pld-status-chip" data-state="{'ready' if st.session_state.database_ready else 'empty'}">
                <span class="pld-status-dot"></span>
                {"Index online" if st.session_state.database_ready else "Index awaiting documents"}
            </span>
            <span class="pld-meta-chip">{total_docs} indexed document{"s" if total_docs != 1 else ""}</span>
            <span class="pld-meta-chip">{total_chunks} searchable chunks</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.space("medium")
render_section_heading(
    "Secure ingestion",
    "Upload one or more PDF files. Processing and indexing use the existing document pipeline.",
)

upload_column, pipeline_column = st.columns([1.55, 1], gap="large")
with upload_column:
    with st.container(border=True):
        st.markdown("### :material/cloud_upload: Add PDF documents")
        st.caption("PDF files only · Batch upload supported · Existing indexed documents are retained")
        uploaded_files = st.file_uploader(
            "Choose PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
            help=(
                "Upload one or more PDF documents. Previously indexed documents "
                "are preserved when navigating between pages."
            ),
        )

        if uploaded_files:
            st.caption(
                f"{len(uploaded_files)} file{'s' if len(uploaded_files) != 1 else ''} "
                "selected for this session."
            )
        else:
            st.caption("Select files above to begin indexing.")

with pipeline_column:
    with st.container(border=True):
        st.markdown("### :material/route: Processing pipeline")
        st.markdown(
            """
            **01 · Extract and split**  
            Read PDF text and create overlapping recursive chunks.

            **02 · Embed and index**  
            Store semantic vectors with source-document metadata in ChromaDB.

            **03 · Sanitize and prepare**  
            Detect sensitive content and create a redacted PDF copy.
            """
        )
        st.caption("Original documents remain unchanged.")

if uploaded_files:
    new_files = [
        file
        for file in uploaded_files
        if file.name not in st.session_state.processed_files
    ]

    if new_files:
        st.space("small")
        st.markdown("#### :material/sync: Processing uploads")
        progress_bar = st.progress(0, text="Preparing document processing…")
        total = len(new_files)

        for idx, file in enumerate(new_files):
            file_bytes = file.getvalue()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_bytes)
                pdf_path = tmp_file.name

            try:
                with st.spinner(f"Indexing '{file.name}' ({idx + 1}/{total})…"):
                    chunks = load_and_split_pdf(pdf_path, doc_name=file.name)

                    if len(st.session_state.documents) == 0:
                        create_vector_store(chunks, reset=True)
                    else:
                        add_documents_to_vector_store(chunks)

                    sanitized_pdf_bytes = sanitize_pdf(file_bytes)

                    st.session_state.documents[file.name] = {
                        "chunks_count": len(chunks),
                        "sanitized_bytes": sanitized_pdf_bytes,
                        "status": "Indexed & Ready",
                    }
                    st.session_state.processed_files.add(file.name)
                    st.session_state.database_ready = True

            except Exception as exc:
                st.error(f"Error processing **{file.name}**: {exc}")

            finally:
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                    except OSError:
                        pass

            progress_bar.progress(
                (idx + 1) / total,
                text=f"Processed {idx + 1} of {total} document(s)",
            )

        progress_bar.empty()
        st.success(f"Successfully indexed {len(new_files)} new document(s).")
        st.rerun()

    elif uploaded_files:
        st.info("All selected documents are already indexed and ready.")

st.space("medium")
render_section_heading(
    "Indexed documents",
    "Document previews show file and index metadata only; source text is not exposed here.",
)

if not documents:
    with st.container(border=True):
        st.markdown("### :material/inventory_2: Your workspace is ready")
        st.write(
            "No documents have been indexed in this session. Upload a PDF above to "
            "populate the knowledge base and enable semantic queries."
        )
        st.caption("The document registry and sanitized exports will appear here after processing.")
else:
    st.markdown(
        f"**{total_docs}** document{'s' if total_docs != 1 else ''} "
        f"· **{total_chunks}** searchable chunk{'s' if total_chunks != 1 else ''}"
    )

    for doc_name, doc_info in documents.items():
        with st.container(border=True):
            details_column, status_column, export_column = st.columns(
                [2.4, 1, 1.3],
                vertical_alignment="center",
            )
            with details_column:
                st.markdown("#### :material/picture_as_pdf: Document preview")
                st.markdown(f"**{doc_name}**")
                st.caption(
                    f"{doc_info['chunks_count']} indexed chunk(s) · "
                    "PDF source · session knowledge base"
                )
            with status_column:
                st.badge(
                    doc_info.get("status", "Indexed & Ready"),
                    icon=":material/check_circle:",
                    color="green",
                )
            with export_column:
                sanitized_bytes = doc_info.get("sanitized_bytes")
                if sanitized_bytes:
                    st.download_button(
                        label="Download sanitized PDF",
                        data=sanitized_bytes,
                        file_name=f"sanitized_{doc_name}",
                        mime="application/pdf",
                        key=f"dl_{doc_name}",
                        width="stretch",
                        help=(
                            "Download the permanently redacted PDF copy. "
                            "The original remains unchanged."
                        ),
                    )
                else:
                    st.warning("Sanitized copy unavailable")

if st.session_state.database_ready:
    st.space("small")
    st.info(
        "Your knowledge base is ready. Open **RAG Query** from the sidebar to "
        "retrieve context from all indexed documents or a selected source."
    )
