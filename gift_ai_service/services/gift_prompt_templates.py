# """
# Prompt templates for generating gift bundles.
# """

# def get_gift_bundle_prompt(user_intent: str, items: list) -> str:
#     """
#     Generate a structured prompt for creating gift bundles.
    
#     Args:
#         user_intent: User's gift search intent
#         items: List of available items
        
#     Returns:
#         str: Formatted prompt for LLM
#     """
#     items_str = "\n".join([
#         f"- {item.get('title', 'Unknown')}: {item.get('description', 'No description')} "
#         f"(Category: {item.get('category', 'Unknown')})"
#         for item in items
#     ])
    
#     prompt = f"""
#     You are a creative gift recommendation expert. Create 3-4 thoughtful gift bundles based on the user's intent and available items.
    
#     USER INTENT: {user_intent}
    
#     AVAILABLE ITEMS:
#     {items_str}
    
#     Create gift bundles with the following structure for each bundle:
#     1. bundle_name: Creative name for the gift bundle
#     2. description: 1-2 sentence explanation of why this bundle is perfect
#     3. items: List of 2-4 items from the available items that go well together
    
#     For each item in the bundle, include:
#     - title: The exact title from available items
#     - reason: Why this item fits the bundle theme
    
#     Requirements:
#     - Use ONLY the available items provided above
#     - Each bundle should have a cohesive theme
#     - Consider different price points and categories
#     - Make the bundles personalized to the user's intent
    
#     Return your response as a valid JSON object with this exact structure:
#     {{
#         "bundles": [
#             {{
#                 "bundle_name": "Creative Bundle Name",
#                 "description": "Why this bundle works well",
#                 "items": [
#                     {{
#                         "title": "Exact item title from available items",
#                         "reason": "Why this item fits the theme"
#                     }}
#                 ]
#             }}
#         ]
#     }}
    
#     Ensure the JSON is valid and properly formatted.
#     """
    
#     return prompt.strip()

# def get_fallback_prompt(user_intent: str, items: list) -> str:
#     """
#     Simplified prompt for fallback LLM models.
    
#     Args:
#         user_intent: User's gift search intent
#         items: List of available items
        
#     Returns:
#         str: Simplified prompt
#     """
#     items_str = "\n".join([
#         f"- {item.get('title', 'Unknown')} ({item.get('category', 'Unknown')})"
#         for item in items
#     ])
    
#     prompt = f"""
#     Create 2-3 gift bundles for: {user_intent}
    
#     Available items:
#     {items_str}
    
#     Return JSON with bundles containing bundle_name, description, and items (each with title and reason).
#     Use only the available items.
#     """
    
#     return prompt.strip()


# gift_ai_service/services/gift_prompt_templates.py
"""
Prompt templates for generating gift bundles.
FIXED: Recipient-aware prompt so the LLM knows to avoid gender-inappropriate items.
"""


def get_gift_bundle_prompt(user_intent: str, items: list) -> str:
    """
    Generate a structured prompt for creating gift bundles.
    The LLM is explicitly instructed to respect recipient context.

    Args:
        user_intent: User's gift search intent (e.g. "birthday gift for mom")
        items:       List of available (pre-filtered) items

    Returns:
        str: Formatted prompt for LLM
    """
    items_str = "\n".join([
        f"- {item.get('title', 'Unknown')}: {item.get('description', 'No description')} "
        f"(Category: {item.get('category', 'Unknown')}, Price: ₹{item.get('price', 0)})"
        for item in items
    ])

    prompt = f"""You are a thoughtful gift recommendation expert with deep knowledge of Indian culture and gifting traditions.

USER'S GIFT REQUEST: "{user_intent}"

AVAILABLE ITEMS (use ONLY these):
{items_str}

YOUR TASK:
Create 1-3 thoughtful gift bundles. Follow these rules strictly:

1. RECIPIENT APPROPRIATENESS: Analyse the recipient from the user's request (e.g. "mom", "dad", "sister").
   - NEVER recommend items clearly meant for the wrong gender or age group.
   - E.g. for "mom" or any female recipient: exclude men's suits, ties, shaving kits, etc.
   - E.g. for "dad" or any male recipient: exclude sarees, kurtis, women's jewellery, etc.
   - If an item is gender-neutral (home decor, art, sweets), it can be included for anyone.

2. COHERENT THEMES: Each bundle should have a clear, cohesive theme (e.g. "Ethnic Elegance", "Home Warmth").

3. HONEST REASONS: For each item, give a specific reason why it suits THIS recipient and occasion.

4. USE ONLY the items listed above. Do not invent items.

Return ONLY a valid JSON object — no markdown, no explanation:
{{
    "bundles": [
        {{
            "bundle_name": "Creative Theme Name",
            "description": "1-2 sentences on why this bundle suits the recipient",
            "items": [
                {{
                    "title": "Exact title from the list above",
                    "reason": "Specific reason this suits the recipient"
                }}
            ]
        }}
    ]
}}"""

    return prompt.strip()


def get_fallback_prompt(user_intent: str, items: list) -> str:
    """
    Simplified prompt for fallback LLM models.

    Args:
        user_intent: User's gift search intent
        items:       List of available items

    Returns:
        str: Simplified prompt
    """
    items_str = "\n".join([
        f"- {item.get('title', 'Unknown')} (₹{item.get('price', 0)}, {item.get('category', 'Unknown')})"
        for item in items
    ])

    prompt = f"""Create 1-2 gift bundles for: "{user_intent}"

Important: Only recommend items that are appropriate for the recipient mentioned in the request.

Available items:
{items_str}

Return JSON with bundles containing bundle_name, description, and items (each with title and reason).
Use only items from the list. Do not include gender-inappropriate items."""

    return prompt.strip()