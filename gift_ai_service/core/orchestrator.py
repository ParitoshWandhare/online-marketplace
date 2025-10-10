"""
core/orchestrator.py
--------------------
Coordinates the full AI-driven gift bundle generation pipeline:
- Extract intent from user query
- Retrieve matching products from vector store
- Validate and rank them
- Generate curated bundle via LLM

Owned by: Member C (Integration + Testing)
"""

from typing import Dict, Any, Optional

from services.gift_intent_service import GiftIntentService
from services.gift_retrieval_service import GiftRetrievalService
from services.gift_validation_service import GiftValidationService
from services.gift_bundle_service import GiftBundleService


class GiftOrchestrator:
    """Main orchestrator to connect all AI services."""

    def __init__(self, llm_client, vector_store):
        self.llm_client = llm_client
        self.vector_store = vector_store

        # Initialize all service components
        self.intent_service = GiftIntentService(llm_client)
        self.retrieval_service = GiftRetrievalService(vector_store)
        self.validation_service = GiftValidationService()
        self.bundle_service = GiftBundleService(llm_client)

    async def generate_bundle_pipeline(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the entire pipeline step-by-step.

        Args:
            query (str): User input like "Gift for parents under 3000"
            user_id (str, optional): Used for personalization or analytics.

        Returns:
            dict: Final curated gift bundle and metadata.
        """
        # 1️⃣ Extract gift intent
        intent = await self.intent_service.extract_intent(query)

        # 2️⃣ Retrieve candidate items
        candidates = await self.retrieval_service.retrieve_items(intent)

        # 3️⃣ Validate + score retrieved items
        validated_items = await self.validation_service.validate_items(candidates, intent)

        # 4️⃣ Generate final bundle
        bundle = await self.bundle_service.create_bundle(validated_items, intent, user_id)

        return bundle
