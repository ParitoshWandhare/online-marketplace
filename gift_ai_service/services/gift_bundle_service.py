"""
services/gift_bundle_service.py
-------------------------------
Uses LLM reasoning to group validated items into final bundles
and generate justification text.

Owned by: Member A
"""

from typing import Dict, Any, List
from .gift_prompt_templates import BUNDLE_GENERATION_PROMPT


class GiftBundleService:
    """Creates curated and themed bundles."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def create_bundle(self, items: List[Dict[str, Any]], intent: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
        """
        Generates a final curated gift bundle via LLM.

        Args:
            items (list[dict]): Validated product candidates.
            intent (dict): Extracted user intent.
            user_id (str, optional): For personalization or tracking.

        Returns:
            dict: Bundle with grouped items and rationale.
        """
        formatted_items = [f"{i['title']} - {i.get('tags', [])}" for i in items]
        prompt = BUNDLE_GENERATION_PROMPT.format(intent=intent, items=formatted_items)
        response = await self.llm_client.run_prompt(prompt)
        return {"bundle": response, "metadata": {"intent": intent, "count": len(items)}}
