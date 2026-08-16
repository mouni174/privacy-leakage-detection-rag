from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split_pdf(
    pdf_path,
    chunk_size=1000,
    chunk_overlap=200
):
    """
    Load a PDF and split it into text chunks.

    Args:
        pdf_path (str): Path to the uploaded PDF.
        chunk_size (int): Maximum size of each chunk.
        chunk_overlap (int): Overlap between chunks.

    Returns:
        list: List of LangChain Document chunks.
    """

    try:
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # Split documents
        chunks = text_splitter.split_documents(documents)

        return chunks

    except Exception as e:
        raise Exception(
            f"PDF loading/chunking error: {e}"
        )