from src.services.search_service import index_item

def test_direct_indexing():
    try:
        result = index_item(
            item_id="test_pottery_001",
            text="Beautiful traditional blue pottery vase from Rajasthan with intricate hand-painted designs",
            payload={
                "title": "Rajasthani Blue Pottery Vase",
                "category": "pottery",
                "material": "ceramic",
                "region": "rajasthan"
            }
        )
        print(f"✓ Indexing successful: {result}")
        return True
    except Exception as e:
        print(f"✗ Indexing failed: {e}")
        return False

test_direct_indexing()