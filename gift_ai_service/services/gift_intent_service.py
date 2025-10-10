"""
services/gift_intent_service.py
-------------------------------
Extracts structured intent from natural language user queries
using LLM prompts.

Owned by: Member A
"""

from typing import Dict, Any
from .gift_prompt_templates import INTENT_EXTRACTION_PROMPT


class GiftIntentService:
    """Detects gift intent such as recipient, occasion, and budget."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def extract_intent(self, query: str) -> Dict[str, Any]:
        """
        Extract intent using LLM.

        Args:
            query (str): Raw user input (e.g. "Gift for sister under ₹2000")

        Returns:
            dict: Parsed structure like:
            {
                "occasion": "birthday",
                "recipient": "sister",
                "budget": 2000,
                "preferences": ["handmade", "cute"]
            }
        """
        prompt = INTENT_EXTRACTION_PROMPT.format(query=query)
        response = await self.llm_client.run_prompt(prompt)
        # TODO: parse response to JSON or dict
        return {"intent_raw": response}
