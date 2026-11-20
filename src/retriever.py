
"""Relevance-filtered retrieval from the current Chroma collection."""

import re
from difflib import SequenceMatcher

from langchain_chroma import Chroma

from src.embeddings import get_embeddings
from src.vector_store import _close_vector_store


# Provisional operational cutoff based on observed live resume-query distances.
# Not validated across a representative document/query dataset.
MAX_L2_DISTANCE = 1.8


def _normalized_content(value: str) -> str:
    """Normalize text before checking for duplicate chunks."""
    return re.sub(r"\s+", " ", value).strip().casefold()


def _is_duplicate(candidate: str, selected: list[str]) -> bool:
    """Return True if the candidate is empty or too similar to a selected chunk."""
    normalized = _normalized_content(candidate)

    if not normalized:
        return True

    return any(
        normalized == previous
        or SequenceMatcher(None, normalized, previous).ratio() >= 0.94
        for previous in selected
    )


def get_relevant_context(
    query,
    collection_name="current_document",
    persist_directory="chroma_db",
    k=3,
    doc_filter=None,
    document_id=None,
    document_ids=None,
):
    """
    Retrieve relevant chunks, optionally scoped to one or more document IDs.

    document_id:
        Retrieves chunks from exactly one document.

    document_ids:
        Retrieves chunks belonging to the supplied document IDs.

    doc_filter:
        Legacy filename-based filter retained for compatibility.

    Returns:
        A dictionary containing retrieved documents and combined context.
    """

    if not query or not query.strip() or k <= 0:
        return {"documents": [], "context": ""}

    # Build the Chroma metadata filter.
    if document_id is not None:
        if not str(document_id).strip():
            return {"documents": [], "context": ""}

        filter_dict = {"document_id": str(document_id)}

    elif document_ids is not None:
        valid_document_ids = [
            str(value).strip()
            for value in document_ids
            if value is not None and str(value).strip()
        ]

        if not valid_document_ids:
            return {"documents": [], "context": ""}

        filter_dict = {"document_id": {"$in": valid_document_ids}}

    elif doc_filter and doc_filter != "All Documents":
        filter_dict = {"source_doc": doc_filter}

    else:
        filter_dict = None

    vector_db = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
    )

    try:
        ranked = vector_db.similarity_search_with_score(
            query,
            k=max(k * 3, k),
            filter=filter_dict,
        )

        selected = []
        selected_content = []

        for document, distance in ranked:

            # Reject chunks outside the provisional distance cutoff.
            if float(distance) > MAX_L2_DISTANCE:
                continue

            # Avoid returning duplicate or near-identical chunks.
            if _is_duplicate(document.page_content, selected_content):
                continue

            selected.append(document)
            selected_content.append(document.page_content)

            if len(selected) >= k:
                break

        return {
            "documents": selected,
            "context": "\n\n".join(
                document.page_content for document in selected
            ),
        }

    finally:
        _close_vector_store(vector_db)
