from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from llm import generate_answer

# Load embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Load ChromaDB
vector_db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)

# User Question
query = input("Ask a question: ")

# Retrieve relevant chunks
results = vector_db.similarity_search(query, k=2)

# Combine retrieved text
context = "\n\n".join(doc.page_content for doc in results)

# Generate answer using Gemini
answer = generate_answer(context, query)

print("\nAnswer:\n")
print(answer)