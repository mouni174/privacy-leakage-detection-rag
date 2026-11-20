"""PDF upload, vector indexing, and sanitized document exports."""

import uuid

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.document_registry import (
    remove_document_from_registry,
    retain_selected_uploads,
    unprocessed_uploads,
)
from src.document_ingest import process_pdf_upload
from src.vector_store import delete_document_from_vector_store
from src.ui import (
    apply_global_styles,
    render_page_header,
    render_section_heading,
    render_sidebar_brand,
    sanitize_sensitive_text,
)

load_dotenv()

st.set_page_config(
    page_title="Document Management | Privacy Leakage Detection",
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

render_page_header(
    title="Document management",
    description=(
        "Bring PDF sources into the private knowledge base. The existing pipeline "
        "extracts and chunks content, indexes it for retrieval, and prepares a "
        "sanitized PDF copy for export."
    ),
    eyebrow="01 / Secure ingestion",
    icon="folder_managed",
    status_label="Index online" if st.session_state.database_ready else "Waiting for PDFs",
)

render_section_heading(
    "Add source documents",
    "Choose PDFs to process through the current extraction, embedding, indexing, and sanitization pipeline.",
)

upload_column, pipeline_column = st.columns([1.7, 1], gap="large")
with upload_column:
    with st.container(border=True):
        st.markdown('<div class="pld-story-index">SOURCE INTAKE</div>', unsafe_allow_html=True)
        st.markdown("### :material/cloud_upload: Select PDF files")
        st.caption("Batch upload supported · Existing indexed documents are retained")
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
        st.markdown('<div class="pld-story-index">PROCESSING ROUTE</div>', unsafe_allow_html=True)
        st.markdown("### :material/route: From source to safe copy")
        st.markdown(
            """
            **01 &nbsp; Extract and split**  
            Read PDF text and create overlapping recursive chunks.

            **02 &nbsp; Embed and index**  
            Store semantic vectors with source-document metadata in ChromaDB.

            **03 &nbsp; Sanitize and prepare**  
            Detect sensitive content and create a redacted PDF copy.
            """
        )
        st.caption("Original documents remain unchanged.")

retain_selected_uploads(st.session_state.seen_uploads, uploaded_files)

if uploaded_files:
    new_files = unprocessed_uploads(
        uploaded_files,
        st.session_state.processed_uploads,
        st.session_state.seen_uploads,
    )

    if new_files:
        st.space("small")
        st.markdown("#### :material/sync: Processing uploads")
        progress_bar = st.progress(0, text="Preparing document processing…")
        total = len(new_files)
        successful_files = 0

        for idx, (file, fingerprint) in enumerate(new_files):
            file_bytes = file.getvalue()
            document_id = str(uuid.uuid4())

            vectors_indexed = False
            try:
                with st.spinner(f"Indexing uploaded PDF {idx + 1} of {total}…"):
                    document_record = process_pdf_upload(
                        file_bytes,
                        file.name,
                        document_id,
                    )
                    vectors_indexed = True

                    document_record["upload_fingerprint"] = fingerprint
                    st.session_state.documents[document_id] = document_record
                    st.session_state.processed_files.add(document_id)
                    st.session_state.processed_uploads[fingerprint] = document_id
                    st.session_state.seen_uploads.add(fingerprint)
                    st.session_state.database_ready = True
                    successful_files += 1

            except Exception as exc:
                st.session_state.documents.pop(document_id, None)
                st.session_state.processed_files.discard(document_id)
                st.session_state.processed_uploads.pop(fingerprint, None)
                if getattr(exc, "rollback_error", None) is not None:
                    st.error(
                        "ChromaDB indexing failed and its document-scoped rollback also "
                        f"failed ({type(exc.rollback_error).__name__}); document ID "
                        f"{document_id} may have orphaned chunks."
                    )
                if vectors_indexed:
                    try:
                        delete_document_from_vector_store(document_id)
                    except Exception as rollback_error:
                        st.error(
                            "Index rollback also failed "
                            f"({type(rollback_error).__name__}); document ID {document_id} "
                            "may have orphaned chunks."
                        )
                st.error(
                    "PDF processing failed "
                    f"({type(exc).__name__}). Check the file format and retry."
                )

            progress_bar.progress(
                (idx + 1) / total,
                text=f"Processed {idx + 1} of {total} document(s)",
            )

        progress_bar.empty()
        if successful_files:
            st.success(f"Successfully indexed {successful_files} new document(s).")
            st.rerun()

    elif uploaded_files:
        st.info("All selected documents are already indexed and ready.")

st.space("medium")
render_section_heading(
    "Knowledge base registry",
    "Review indexed document metadata and retrieve permanently sanitized PDF exports. Source text is not exposed here.",
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

    for registry_key, doc_info in list(documents.items()):
        document_id = doc_info.get("document_id")
        display_name = doc_info.get("original_filename", registry_key)
        with st.container(border=True):
            safe_doc_name = sanitize_sensitive_text(display_name)
            details_column, status_column, export_column = st.columns(
                [2.4, 1, 1.3],
                vertical_alignment="center",
            )
            with details_column:
                st.markdown("#### :material/picture_as_pdf: Document preview")
                st.markdown(f"**{safe_doc_name}**")
                st.caption(
                    f"{doc_info['chunks_count']} indexed chunk(s) · "
                    "PDF source · session knowledge base"
                )
                st.caption(
                    f"Document ID: {document_id[:12]}…"
                    if document_id
                    else "Document ID: legacy filename-based record"
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
                        file_name=f"sanitized_{safe_doc_name}",
                        mime="application/pdf",
                        key=f"dl_{document_id or registry_key}",
                        width="stretch",
                        help=(
                            "Download the permanently redacted PDF copy. "
                            "The original remains unchanged."
                        ),
                    )
                else:
                    st.warning("Sanitized copy unavailable")

            if document_id:
                confirm_delete = st.checkbox(
                    f"Confirm deletion of {safe_doc_name}",
                    key=f"confirm_delete_{document_id}",
                )
                delete_col, _ = st.columns([1.3, 4])
                with delete_col:
                    if st.button(
                        "Delete document",
                        key=f"delete_document_{document_id}",
                        type="secondary",
                        icon=":material/delete:",
                        width="stretch",
                    ):
                        if not confirm_delete:
                            st.warning("Confirm the deletion before continuing.")
                        else:
                            try:
                                deleted_count = delete_document_from_vector_store(document_id)
                            except Exception as exc:
                                st.error(
                                    "Document deletion failed; the registry entry was retained "
                                    f"({type(exc).__name__})."
                                )
                            else:
                                if deleted_count == 0:
                                    st.error(
                                        "No indexed chunks were found; the registry entry was retained."
                                    )
                                else:
                                    try:
                                        remove_document_from_registry(
                                            st.session_state,
                                            registry_key,
                                            document_id,
                                        )
                                    except Exception as exc:
                                        st.error(
                                            "Vectors were deleted, but the session registry could not "
                                            f"be updated ({type(exc).__name__})."
                                        )
                                    else:
                                        st.success(
                                            f"Deleted {safe_doc_name} and {deleted_count} indexed chunk(s)."
                                        )
                                        st.rerun()
            else:
                st.caption(
                    "Safe deletion is unavailable for this legacy record because its "
                    "stored vectors have no document ID."
                )

if st.session_state.database_ready:
    st.space("small")
    st.info(
        "Your knowledge base is ready. Open **RAG Query** from the sidebar to "
        "retrieve context from all indexed documents or a selected source."
    )
