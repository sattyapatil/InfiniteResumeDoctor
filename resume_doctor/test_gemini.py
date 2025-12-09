import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Testing API Key: {api_key[:5]}...")

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    response = model.generate_content("Hello, can you hear me?")
    print("Success!")
    print(response.text)
except Exception as e:
    print("Error:")
    print(e)
