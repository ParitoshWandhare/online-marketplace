# simple_gemini_test.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"API Key exists: {bool(api_key)}")
    print(f"API Key length: {len(api_key) if api_key else 0}")
    
    if not api_key:
        print("ERROR: No API key found in .env file")
        return False
    
    # Configure genai
    genai.configure(api_key=api_key)
    
    try:
        print("Testing embedding generation...")
        result = genai.embed_content(
            model="models/embedding-001",
            content="hello world test"
        )
        
        print(f"SUCCESS! Embedding dimensions: {len(result['embedding'])}")
        print(f"First 5 values: {result['embedding'][:5]}")
        return True
        
    except Exception as e:
        print(f"EMBEDDING ERROR: {e}")
        
        try:
            print("Trying to list available models...")
            models = list(genai.list_models())
            embedding_models = [m for m in models if 'embed' in m.name.lower()]
            print(f"Available embedding models: {[m.name for m in embedding_models]}")
        except Exception as e2:
            print(f"MODEL LISTING ERROR: {e2}")
            
        return False

if __name__ == "__main__":
    test_gemini() 