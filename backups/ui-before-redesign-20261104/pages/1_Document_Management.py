"""
pages/1_Document_Management.py
-------------------------------
Feature 2 + Feature 3 – PDF upload, indexing, and sanitized-PDF export.

Purpose: Manage uploaded PDFs.
Includes:
  • Multiple PDF upload
  • Uploaded document list
  • Document names and chunk counts
  • Indexing status
  • Per-document sanitized PDF download
  • Clear indication of successfully indexed documents

No RAG question-answering interface or full privacy dashboard lives here.
"""

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from src.session_init import init_session_state
from src.loader import load_and_split_pdf
from src.vector_store import create_vector_store, add_documents_to_vector_store
from src.pdf_sanitizer import sanitize_pdf

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Document Management – Privacy RAG",
    page_icon="📄",
    layout="wide"
)

# ── Session state ──────────────────────────────────────────────────────────────
init_session_state()

# ── Page title & description ───────────────────────────────────────────────────
st.title("📄 Document Management")
st.markdown(
    "Upload one or more PDF documents. Each document is chunked with `source_doc` metadata, "
    "indexed into the shared ChromaDB vector collection, and processed with PyMuPDF "
    "to generate a permanently sanitized PDF ready for download."
)

st.markdown("---")

# ── Upload widget ──────────────────────────────────────────────────────────────
st.subheader("📤 Upload PDF Documents")

uploaded_files = st.file_uploader(
    "Select PDF files to index into the knowledge base",
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload single or multiple PDF documents. Previously uploaded documents are preserved across navigation."
)

# ── Process new uploads ────────────────────────────────────────────────────────
if uploaded_files:
    new_files = [
        f for f in uploaded_files
        if f.name not in st.session_state.processed_files
    ]

    if new_files:
        progress_bar = st.progress(0, text="Processing documents…")
        total = len(new_files)

        for idx, file in enumerate(new_files):
            file_bytes = file.getvalue()

            # Write to a temporary file so the PDF loader can use a file path
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as tmp_file:
                tmp_file.write(file_bytes)
                pdf_path = tmp_file.name

            try:
                with st.spinner(f"Indexing '{file.name}' ({idx + 1}/{total})…"):

                    # 1. Chunk the PDF with source_doc metadata (Feature 3)
                    chunks = load_and_split_pdf(
                        pdf_path,
                        doc_name=file.name
                    )

                    # 2. Index into Chroma
                    #    First document resets the collection; subsequent ones append
                    if len(st.session_state.documents) == 0:
                        create_vector_store(chunks, reset=True)
                    else:
                        add_documents_to_vector_store(chunks)

                    # 3. Generate sanitized PDF (Feature 2 – true PyMuPDF redaction)
                    sanitized_pdf_bytes = sanitize_pdf(file_bytes)

                    # 4. Register in session state document registry
                    st.session_state.documents[file.name] = {
                        "chunks_count": len(chunks),
                        "sanitized_bytes": sanitized_pdf_bytes,
                        "status": "Indexed & Ready"
                    }
                    st.session_state.processed_files.add(file.name)
                    st.session_state.database_ready = True

            except Exception as exc:
                st.error(f"❌ Error processing **{file.name}**: {exc}")

            finally:
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                    except OSError:
                        pass

            progress_bar.progress(
                (idx + 1) / total,
                text=f"Processed {idx + 1} of {total} document(s)"
            )

        progress_bar.empty()
        st.success(f"✅ Successfully indexed {len(new_files)} new document(s).")
        st.rerun()

    else:
        if uploaded_files:
            st.info("ℹ️ All selected documents are already indexed and ready.")


# ── Document Registry ──────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📚 Uploaded Document List")

if not st.session_state.documents:
    st.info("No documents uploaded yet. Upload one or more PDFs above to populate the registry.")
else:
    total_docs = len(st.session_state.documents)
    total_chunks = sum(
        d["chunks_count"] for d in st.session_state.documents.values()
    )

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("📄 Total Indexed Documents", total_docs)
    col_m2.metric("🧩 Total Chunks in ChromaDB", total_chunks)

    st.markdown("#### Document Index Status & Sanitized Copies")

    for doc_name, doc_info in st.session_state.documents.items():
        with st.expander(f"📄 {doc_name}", expanded=True):
            col_a, col_b, col_c = st.columns([2, 1, 1.5])
            with col_a:
                st.markdown(f"**Document Name:** `{doc_name}`")
                st.markdown(f"**Chunk Count:** `{doc_info['chunks_count']}` chunk(s)")
            with col_b:
                st.markdown("**Indexing Status:**")
                st.success("✅ Indexed & Ready")
            with col_c:
                st.markdown("**Sanitized PDF:**")
                if doc_info.get("sanitized_bytes"):
                    st.download_button(
                        label="📥 Download Sanitized PDF",
                        data=doc_info["sanitized_bytes"],
                        file_name=f"sanitized_{doc_name}",
                        mime="application/pdf",
                        key=f"dl_{doc_name}",
                        use_container_width=True,
                        help=f"Download the privacy-sanitized version of {doc_name} with all PII permanently redacted."
                    )
                else:
                    st.warning("Sanitization unavailable")

# ── Navigation hint ────────────────────────────────────────────────────────────
if st.session_state.database_ready:
    st.markdown("---")
    st.info(
        "💡 **Next Step:** Navigate to **🔍 RAG Query** in the sidebar to ask questions "
        "across your indexed documents."
    )
