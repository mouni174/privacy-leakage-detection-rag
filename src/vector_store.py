from langchain_chroma import Chroma

from src.embeddings import get_embeddings


def create_vector_store(
    chunks,
    persist_directory="chroma_db",
    collection_name="current_document"
):
    """
    Create a fresh Chroma vector database for the current document.

    Any existing collection with the same name is deleted first,
    preventing chunks from previously uploaded documents from
    being retrieved.
    """

    try:
        embeddings = get_embeddings()

        # Open existing Chroma collection
        existing_db = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
            collection_name=collection_name
        )

        # Remove all chunks from the previous document
        existing_db.delete_collection()

        # Create a fresh collection for the new document
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