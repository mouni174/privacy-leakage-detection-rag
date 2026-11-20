

"""Orchestrate PDF preparation before committing it to the vector store."""

import os
import tempfile

from src.loader import load_and_split_pdf
from src.pdf_sanitizer import sanitize_pdf
from src.vector_store import (
    _close_vector_store,
    add_documents_to_vector_store,
)


def process_pdf_upload(file_bytes, filename, document_id):
    """Extract, sanitize, and index one PDF under its unique document ID."""

    if not document_id or not str(document_id).strip():
        raise ValueError("A non-empty document ID is required for PDF ingestion.")

    document_id = str(document_id).strip()
    pdf_path = None
    vector_db = None
    indexing_started = False

    try:
        # Save uploaded PDF temporarily.
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as tmp_file:
            pdf_path = tmp_file.name
            tmp_file.write(file_bytes)

        # Extract text and create chunks.
        chunks = load_and_split_pdf(
            pdf_path,
            doc_name=filename,
            document_id=document_id,
        )

        if not chunks:
            raise ValueError("The PDF did not contain extractable text.")

        # Sanitize PDF before returning it to the caller.
        sanitized_pdf_bytes = sanitize_pdf(file_bytes)

        # Index document chunks.
        indexing_started = True
        vector_db = add_documents_to_vector_store(
            chunks,
            document_id=document_id,
        )

        return {
            "document_id": document_id,
            "original_filename": filename,
            "chunks_count": len(chunks),
            "sanitized_bytes": sanitized_pdf_bytes,
            "status": "Indexed & Ready",
        }

    except Exception:
        # Attempt to remove partially indexed vectors.
        if indexing_started:
            rollback_db = None

            try:
                from langchain_chroma import Chroma
                from src.embeddings import get_embeddings

                rollback_db = Chroma(
                    collection_name="current_document",
                    persist_directory="chroma_db",
                    embedding_function=get_embeddings(),
                )

                rollback_db.delete(
                    where={"document_id": document_id}
                )

            except Exception as rollback_error:
                raise RuntimeError(
                    f"PDF ingestion failed and rollback also failed: "
                    f"{rollback_error}"
                ) from rollback_error

            finally:
                if rollback_db is not None:
                    _close_vector_store(rollback_db)

        raise

    finally:
        if vector_db is not None:
            _close_vector_store(vector_db)

        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except OSError:
                pass
