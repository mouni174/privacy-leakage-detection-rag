from langchain_chroma import Chroma

from src.embeddings import get_embeddings


def create_vector_store(
    chunks,
    persist_directory="chroma_db",
    collection_name="current_document",
    reset=True
):
    """
    Create or update a Chroma vector database.

    Args:
        chunks (list): List of Document chunks.
        persist_directory (str): Directory for vector store persistence.
        collection_name (str): Collection name in Chroma.
        reset (bool): If True, clears existing collection first. If False, appends.
    """

    try:
        embeddings = get_embeddings()

        if reset:
            # Open existing Chroma collection and delete previous contents
            existing_db = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings,
                collection_name=collection_name
            )
            existing_db.delete_collection()

        # Add chunks to collection
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory,
            collection_name=collection_name
        )

        return vector_db

    except Exception as e:
        raise Exception(
            f"Error creating vector store: {e}"
        )


def add_documents_to_vector_store(
    chunks,
    persist_directory="chroma_db",
    collection_name="current_document"
):
    """
    Add document chunks to the existing vector store without resetting.
    """
    return create_vector_store(
        chunks,
        persist_directory=persist_directory,
        collection_name=collection_name,
        reset=False
    )