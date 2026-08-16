from langchain_chroma import Chroma

from src.embeddings import get_embeddings


def get_relevant_context(
    query,
    collection_name="current_document",
    persist_directory="chroma_db",
    k=3
):
    """
    Retrieve the most relevant document chunks
    for a user query.
    """

    try:

        vector_db = Chroma(
            collection_name=collection_name,
            persist_directory=persist_directory,
            embedding_function=get_embeddings()
        )

        documents = vector_db.similarity_search(
            query,
            k=k
        )

        context = "\n\n".join(
            document.page_content
            for document in documents
        )

        return {
            "documents": documents,
            "context": context
        }

    except Exception as e:

        raise Exception(
            f"Retriever Error: {e}"
        )