from langchain_chroma import Chroma

from src.embeddings import get_embeddings


def create_vector_store(
    chunks,
    persist_directory="chroma_db",
    collection_name="current_document"
):
    """
    Create and persist a Chroma vector database
    from document chunks.
    """

    try:

        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=get_embeddings(),
            persist_directory=persist_directory,
            collection_name=collection_name
        )

        return vector_db

    except Exception as e:

        raise Exception(
            f"Error creating vector store: {e}"
        )