import os

import google.generativeai as genai

# Manual .env parsing
try:
    with open(".env.local") as f:
        for line in f:
            if "GOOGLE_API_KEY" in line:
                # Split only on first =
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                os.environ["GOOGLE_API_KEY"] = key
                break
except FileNotFoundError:
    pass

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # try .env
    try:
        with open(".env") as f:
            for line in f:
                if "GOOGLE_API_KEY" in line:
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["GOOGLE_API_KEY"] = key
                    break
    except FileNotFoundError:
        pass

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env.local or .env")
    exit(1)

genai.configure(api_key=api_key)

print("List of available models:")
try:
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
