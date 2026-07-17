import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_answer(context, question):
    prompt = f"""
You are an enterprise document assistant.

Answer ONLY using the information provided below.

Context:
{context}

Question:
{question}

If the answer is not available in the context, reply:
"I couldn't find that information in the provided documents."
"""

    response = client.models.generate_content(
       model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    return response.text