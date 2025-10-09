from src.services.embedding_service import get_embedding

def test_embeddings():
    try:
        test_text = "Traditional blue pottery from Rajasthan"
        embedding = get_embedding(test_text)
        print(f"✓ Embedding generated: {len(embedding)} dimensions")
        return True
    except Exception as e:
        print(f"✗ Embedding generation failed: {e}")
        return False

test_embeddings()