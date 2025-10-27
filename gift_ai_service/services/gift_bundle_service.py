# gift_ai_service/services/gift_bundle_service.py
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GiftBundleService:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_bundles(self, intent: dict, valid_items: List[Dict]) -> Dict[str, Any]:
        bundles = []
        for item in valid_items[:3]:
            bundles.append({
                "id": item.get("_id"),
                "title": item.get("title", "Handmade Gift"),
                "price": item.get("price", 999),
                "story": f"A warm handmade gift for your {intent['recipient']} on their {intent['occasion']}!",
                "packaging": "Eco-friendly box with ribbon",
                "similarity": 0.94
            })
        return {"bundles": bundles}