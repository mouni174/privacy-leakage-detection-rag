import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

print("API Key Found:", api_key is not None)

client = genai.Client(api_key=api_key)

try:
    models = client.models.list()

    print("\nAvailable Models:")
    for model in models:
        print(model.name)

except Exception as e:
    print("\nError:")
    print(e)