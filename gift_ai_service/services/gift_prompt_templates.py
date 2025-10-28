"""
Prompt templates for generating gift bundles.
"""

def get_gift_bundle_prompt(user_intent: str, items: list) -> str:
    """
    Generate a structured prompt for creating gift bundles.
    
    Args:
        user_intent: User's gift search intent
        items: List of available items
        
    Returns:
        str: Formatted prompt for LLM
    """
    items_str = "\n".join([
        f"- {item.get('title', 'Unknown')}: {item.get('description', 'No description')} "
        f"(Category: {item.get('category', 'Unknown')})"
        for item in items
    ])
    
    prompt = f"""
    You are a creative gift recommendation expert. Create 3-4 thoughtful gift bundles based on the user's intent and available items.
    
    USER INTENT: {user_intent}
    
    AVAILABLE ITEMS:
    {items_str}
    
    Create gift bundles with the following structure for each bundle:
    1. bundle_name: Creative name for the gift bundle
    2. description: 1-2 sentence explanation of why this bundle is perfect
    3. items: List of 2-4 items from the available items that go well together
    
    For each item in the bundle, include:
    - title: The exact title from available items
    - reason: Why this item fits the bundle theme
    
    Requirements:
    - Use ONLY the available items provided above
    - Each bundle should have a cohesive theme
    - Consider different price points and categories
    - Make the bundles personalized to the user's intent
    
    Return your response as a valid JSON object with this exact structure:
    {{
        "bundles": [
            {{
                "bundle_name": "Creative Bundle Name",
                "description": "Why this bundle works well",
                "items": [
                    {{
                        "title": "Exact item title from available items",
                        "reason": "Why this item fits the theme"
                    }}
                ]
            }}
        ]
    }}
    
    Ensure the JSON is valid and properly formatted.
    """
    
    return prompt.strip()

def get_fallback_prompt(user_intent: str, items: list) -> str:
    """
    Simplified prompt for fallback LLM models.
    
    Args:
        user_intent: User's gift search intent
        items: List of available items
        
    Returns:
        str: Simplified prompt
    """
    items_str = "\n".join([
        f"- {item.get('title', 'Unknown')} ({item.get('category', 'Unknown')})"
        for item in items
    ])
    
    prompt = f"""
    Create 2-3 gift bundles for: {user_intent}
    
    Available items:
    {items_str}
    
    Return JSON with bundles containing bundle_name, description, and items (each with title and reason).
    Use only the available items.
    """
    
    return prompt.strip()