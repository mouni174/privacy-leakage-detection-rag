import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Check current working directory
print("Current Working Directory:", os.getcwd())

# Load the PDF
loader = PyPDFLoader("data/sample.pdf")
documents = loader.load()

print("Number of Pages:", len(documents))

# Create the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20
)

# Split the document into chunks
chunks = text_splitter.split_documents(documents)

print("Number of Chunks:", len(chunks))

# Display each chunk
for i, chunk in enumerate(chunks):
    print(f"\n------ Chunk {i + 1} ------")
    print(chunk.page_content)