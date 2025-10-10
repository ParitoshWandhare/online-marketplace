"""
services/gift_prompt_templates.py
---------------------------------
Houses reusable prompt templates for intent extraction and bundle creation.
"""

INTENT_EXTRACTION_PROMPT = """
You are an assistant that extracts structured gift intent from text.
User Query: "{query}"

Return a JSON object with:
- recipient
- occasion
- budget (numeric)
- preferences (list)
"""

BUNDLE_GENERATION_PROMPT = """
You are an expert gift recommender.
Given this intent: {intent}
And these shortlisted items: {items}

Group them into a cohesive gift bundle and justify your reasoning.
Return concise JSON:
{
  "bundle_name": "...",
  "items": [...],
  "reasoning": "..."
}
"""
