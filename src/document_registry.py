"""Small, deterministic helpers for session-scoped upload tracking."""

import hashlib


def upload_fingerprint(file_bytes: bytes) -> str:
    """Return a content fingerprint used only to suppress rerun re-indexing."""
    return hashlib.sha256(file_bytes).hexdigest()


def unprocessed_uploads(uploaded_files, processed_uploads, seen_uploads=None):
    """Return each unseen content upload once, regardless of filename."""
    seen = set(processed_uploads)
    if seen_uploads is not None:
        seen.update(seen_uploads)
    result = []
    for uploaded_file in uploaded_files:
        fingerprint = upload_fingerprint(uploaded_file.getvalue())
        if fingerprint not in seen:
            result.append((uploaded_file, fingerprint))
            seen.add(fingerprint)
    return result


def retain_selected_uploads(seen_uploads, uploaded_files):
    """Keep deletion tombstones only while the same bytes remain selected."""
    selected_fingerprints = {
        upload_fingerprint(uploaded_file.getvalue())
        for uploaded_file in (uploaded_files or [])
    }
    seen_uploads.intersection_update(selected_fingerprints)


def remove_document_from_registry(session_state, registry_key, document_id):
    """Remove one matching UUID entry and its session upload tracking."""
    documents = session_state["documents"]
    info = documents.get(registry_key)
    if info is None or info.get("document_id") != document_id:
        raise ValueError("The selected registry entry does not match this document ID.")

    fingerprint = info.get("upload_fingerprint")
    del documents[registry_key]
    session_state["processed_files"].discard(document_id)
    if fingerprint:
        session_state["processed_uploads"].pop(fingerprint, None)
    if session_state.get("selected_document_id") == document_id:
        session_state["selected_document_id"] = None
        session_state["selected_scope"] = "All Documents"
    latest = session_state.get("last_query_result")
    if latest and latest.get("target_document_id") == document_id:
        session_state["last_query_result"] = None
    session_state["database_ready"] = any(
        entry.get("document_id") for entry in documents.values()
    )
