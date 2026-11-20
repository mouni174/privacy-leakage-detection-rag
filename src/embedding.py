from sentence_transformers import SentenceTransformer

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Sample sentence
text = "Artificial Intelligence is transforming healthcare."

# Generate embedding
embedding = model.encode(text)
