import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split_pdf(
    pdf_path,
    chunk_size=1000,
    chunk_overlap=200,
    doc_name=None
):
    """
    Load a PDF and split it into text chunks.

    Args:
        pdf_path (str): Path to the uploaded PDF.
        chunk_size (int): Maximum size of each chunk.
        chunk_overlap (int): Overlap between chunks.
        doc_name (str, optional): Name of the source document.

    Returns:
        list: List of LangChain Document chunks.
    """

    try:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be non-negative and smaller than chunk_size."
            )

        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Determine document name
        source_name = doc_name or os.path.basename(pdf_path)

        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Split documents
        chunks = text_splitter.split_documents(documents)

        # Tag every chunk with source_doc metadata
        for chunk in chunks:
            chunk.metadata["source_doc"] = source_name

        return chunks

    except Exception as e:
        raise Exception(
            f"PDF loading/chunking error: {e}"
        )