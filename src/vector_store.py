
"""Document-scoped operations for the persistent Chroma collection."""

from uuid import uuid4

from langchain_chroma import Chroma

from src.embeddings import get_embeddings


class VectorStoreWriteError(RuntimeError):
    """Raised when indexing fails, with rollback outcome attached."""

    def __init__(self, message, rollback_error=None):
        super().__init__(message)
        self.rollback_error = rollback_error


def _document_id_from_chunks(chunks):
    ids = {chunk.metadata.get("document_id") for chunk in chunks}
    ids.discard(None)

    if len(ids) > 1:
        raise ValueError("All chunks must belong to the same document ID.")

    return next(iter(ids), None)


def _prepare_chunks(chunks, document_id=None):
    if not chunks:
        raise ValueError("Cannot index a document with no text chunks.")

    if document_id is not None and not str(document_id).strip():
        raise ValueError("document_id cannot be blank.")

    existing_id = _document_id_from_chunks(chunks)

    stable_id = str(
        document_id if document_id is not None else existing_id or uuid4()
    )

    if existing_id is not None and existing_id != stable_id:
        raise ValueError("Provided document ID does not match chunk metadata.")

    for chunk in chunks:
        chunk.metadata["document_id"] = stable_id

    return stable_id


def _chunk_ids(chunks):
    document_id = _document_id_from_chunks(chunks)

    if document_id is None:
        raise ValueError("Chunks must have a document ID.")

    return [
        f"{document_id}:{index}"
        for index in range(len(chunks))
    ]


def _open_vector_store(persist_directory, collection_name):
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
        collection_name=collection_name,
    )


def _close_vector_store(vector_db):
    """Release the persistent Chroma client when an operation owns it."""
    if vector_db is None:
        return

    client = getattr(vector_db, "_client", None)
    close = getattr(client, "close", None)

    if callable(close):
        close()


def create_vector_store(
    chunks,
    persist_directory="chroma_db",
    collection_name="current_document",
    reset=False,
):
    """Create or append to the vector store.

    Collection reset requires explicit opt-in.
    """
    if not reset:
        return add_documents_to_vector_store(
            chunks,
            persist_directory=persist_directory,
            collection_name=collection_name,
        )

    _prepare_chunks(chunks)

    vector_db = _open_vector_store(
        persist_directory,
        collection_name,
    )

    try:
        vector_db.delete_collection()
    finally:
        _close_vector_store(vector_db)

    vector_db = _open_vector_store(
        persist_directory,
        collection_name,
    )

    try:
        vector_db.add_documents(
            documents=chunks,
            ids=_chunk_ids(chunks),
        )
        return vector_db
    except Exception as exc:
        _close_vector_store(vector_db)
        raise RuntimeError(
            f"Error creating vector store: {exc}"
        ) from exc


def add_documents_to_vector_store(
    chunks,
    persist_directory="chroma_db",
    collection_name="current_document",
    document_id=None,
):
    """Append one document without resetting existing records."""
    stable_id = _prepare_chunks(chunks, document_id)

    if document_id_exists(
        stable_id,
        persist_directory,
        collection_name,
    ):
        raise ValueError(f"Document ID already exists: {stable_id}")

    vector_db = _open_vector_store(
        persist_directory,
        collection_name,
    )

    chunk_ids = _chunk_ids(chunks)

    try:
        vector_db.add_documents(
            documents=chunks,
            ids=chunk_ids,
        )

        stored_ids = vector_db.get(
            where={"document_id": stable_id}
        ).get("ids", [])

        if set(stored_ids) != set(chunk_ids):
            raise RuntimeError(
                f"Indexed chunk verification failed for document {stable_id}."
            )

        return vector_db

    except Exception as exc:
        rollback_error = None

        try:
            vector_db.delete(
                where={"document_id": stable_id}
            )
        except Exception as rollback_exc:
            rollback_error = rollback_exc

        _close_vector_store(vector_db)

        raise VectorStoreWriteError(
            f"Error adding document {stable_id}: {exc}",
            rollback_error=rollback_error,
        ) from exc


def document_id_exists(
    document_id,
    persist_directory="chroma_db",
    collection_name="current_document",
):
    """Check whether chunks exist for a document ID."""
    if not document_id:
        return False

    vector_db = None

    try:
        vector_db = _open_vector_store(
            persist_directory,
            collection_name,
        )

        return bool(
            vector_db.get(
                where={"document_id": str(document_id)}
            ).get("ids")
        )

    except Exception as exc:
        raise RuntimeError(
            f"Could not check document {document_id}: {exc}"
        ) from exc

    finally:
        if vector_db is not None:
            _close_vector_store(vector_db)


def delete_document_from_vector_store(
    document_id,
    persist_directory="chroma_db",
    collection_name="current_document",
):
    """Delete only chunks belonging to one document ID."""
    if not document_id:
        raise ValueError("document_id is required for document deletion.")

    vector_db = None

    try:
        vector_db = _open_vector_store(
            persist_directory,
            collection_name,
        )

        matches = vector_db.get(
            where={"document_id": str(document_id)}
        ).get("ids", [])

        if not matches:
            return 0

        vector_db.delete(
            where={"document_id": str(document_id)}
        )

        remaining = vector_db.get(
            where={"document_id": str(document_id)}
        ).get("ids", [])

        if remaining:
            raise RuntimeError(
                f"ChromaDB retained chunks for document {document_id}."
            )

        return len(matches)

    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise

        raise RuntimeError(
            f"Could not delete document {document_id}: {exc}"
        ) from exc

    finally:
        if vector_db is not None:
            _close_vector_store(vector_db)
