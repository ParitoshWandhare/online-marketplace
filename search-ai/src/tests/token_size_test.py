# token_size_test.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import tiktoken  # For token counting (optional)

# Load environment variables
load_dotenv()

def count_tokens_approximate(text: str) -> int:
    """Approximate token count - Gemini uses similar tokenization to GPT"""
    try:
        # This is an approximation - actual Gemini tokenization may differ
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4

def test_embedding_sizes():
    """Test what size texts your search pipeline is actually sending to Gemini"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: No API key found")
        return
        
    genai.configure(api_key=api_key)
    
    # Test different text sizes
    test_cases = [
        ("small", "blue pottery"),
        ("medium", "blue pottery ceramic bowl handmade kitchen artisan craft"),
        ("large", "blue pottery ceramic bowl handmade kitchen artisan craft " * 10),
        ("very_large", "blue pottery ceramic bowl handmade kitchen artisan craft " * 50),
        ("huge", "blue pottery ceramic bowl handmade kitchen artisan craft " * 100)
    ]
    
    for size_name, text in test_cases:
        char_count = len(text)
        token_estimate = count_tokens_approximate(text)
        
        print(f"\n--- Testing {size_name.upper()} text ---")
        print(f"Characters: {char_count}")
        print(f"Estimated tokens: {token_estimate}")
        print(f"Text preview: {text[:100]}...")
        
        # Test if this size works
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=text
            )
            print(f"✅ SUCCESS - Embedding generated ({len(result['embedding'])} dimensions)")
            
        except Exception as e:
            print(f"❌ FAILED - {e}")
            if "quota" in str(e).lower():
                print("   → This is a quota issue, not a size issue")
                break
            elif "token" in str(e).lower() or "limit" in str(e).lower():
                print(f"   → This text ({token_estimate} tokens) exceeds the limit")
                break

def test_your_search_pipeline():
    """Test the actual texts your search service would generate"""
    
    # Import your services to test what they actually send
    try:
        from src.services.query_enhancer import enhance_query
        from src.services.embedding_service import get_embedding
        
        test_query = "blue pottery bowl"
        
        print(f"\n--- Testing Your Search Pipeline ---")
        print(f"Original query: '{test_query}'")
        print(f"Query length: {len(test_query)} chars, ~{count_tokens_approximate(test_query)} tokens")
        
        # Test query expansion
        try:
            expanded_queries = enhance_query(test_query, topn=3)
            print(f"\nExpanded queries:")
            for i, exp_query in enumerate(expanded_queries):
                tokens = count_tokens_approximate(exp_query)
                print(f"  {i+1}. '{exp_query}' ({len(exp_query)} chars, ~{tokens} tokens)")
                
                # Check if any expansion is unusually large
                if tokens > 100:
                    print(f"    ⚠️  WARNING: This expansion is large ({tokens} tokens)")
                    
        except Exception as e:
            print(f"Query expansion error: {e}")
            
    except ImportError as e:
        print(f"Cannot import your services: {e}")
        print("Run this from your project root directory")

def test_gemini_token_limits():
    """Test Gemini's actual token limits"""
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return
        
    genai.configure(api_key=api_key)
    
    # Test progressively larger inputs to find the limit
    base_text = "test " * 100  # 400 characters
    
    for multiplier in [1, 2, 5, 10, 25, 50]:
        test_text = base_text * multiplier
        tokens = count_tokens_approximate(test_text)
        
        print(f"\n--- Testing {tokens} tokens ---")
        
        if tokens > 1000:  # Gemini embedding limit is 1000 tokens
            print(f"❌ SKIPPING - {tokens} tokens exceeds known 1000 token limit")
            continue
            
        try:
            result = genai.embed_content(
                model="models/embedding-001",
                content=test_text
            )
            print(f"✅ SUCCESS - {tokens} tokens processed")
            
        except Exception as e:
            print(f"❌ FAILED - {tokens} tokens: {e}")
            break

if __name__ == "__main__":
    print("=== Token Size Testing ===")
    
    # Install tiktoken if needed
    try:
        import tiktoken
    except ImportError:
        print("Installing tiktoken for token counting...")
        os.system("pip install tiktoken")
        import tiktoken
    
    print("\n1. Testing different text sizes...")
    test_embedding_sizes()
    
    print("\n2. Testing your actual search pipeline...")
    test_your_search_pipeline()
    
    print("\n3. Testing Gemini token limits...")
    test_gemini_token_limits()