
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# Load PDF
loader = PyPDFLoader("data/sample.pdf")
documents = loader.load()

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)

chunks = text_splitter.split_documents(documents)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embedding for each chunk
embeddings = []

for chunk in chunks:
    embedding = model.encode(chunk.page_content)
    embeddings.append(embedding)
