"""Relevance-filtered retrieval from the current Chroma collection."""

import re
from difflib import SequenceMatcher

from langchain_chroma import Chroma

from src.embeddings import get_embeddings


# Calibrated on the labeled Phase 5 training split; see reports/phase5_retrieval_report.md.
MAX_L2_DISTANCE = 0.792106568813324


def _normalized_content(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _is_duplicate(candidate: str, selected: list[str]) -> bool:
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
):
    """Return only unique chunks within the evaluated Chroma L2 relevance range."""
    if not query or not query.strip() or k <= 0:
        return {"documents": [], "context": ""}

    vector_db = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
    )
    filter_dict = (
        {"source_doc": doc_filter}
        if doc_filter and doc_filter != "All Documents"
        else None
    )
    ranked = vector_db.similarity_search_with_score(
        query,
        k=max(k * 3, k),
        filter=filter_dict,
    )

    selected = []
    selected_content = []
    for document, distance in ranked:
        if float(distance) > MAX_L2_DISTANCE:
            continue
        if _is_duplicate(document.page_content, selected_content):
            continue
        selected.append(document)
        selected_content.append(document.page_content)
        if len(selected) == k:
            break

    return {
        "documents": selected,
        "context": "\n\n".join(document.page_content for document in selected),
    }
