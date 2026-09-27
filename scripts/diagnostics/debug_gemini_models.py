import google.generativeai as genai
import os
import keyring

# Try to get key from keyring or env
api_key = keyring.get_password("AutoSub-AI", "gemini_api_key") or os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API Key not found!")
else:
    genai.configure(api_key=api_key)
    print("Listing available models...")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
