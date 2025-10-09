# genai-services/src/vision_ai/prompts/prompt_engineering.py
def get_story_prompt(craft_type: str, language: str, tone: str) -> str:
    # Craft-specific guidance
    craft_guidelines = {
        "pottery": "Emphasize wheel-throwing or hand-building techniques, clay types, firing processes, and cultural context (e.g., regional traditions).",
        "basket": "Focus on weaving patterns, natural fibers, traditional craftsmanship, and cultural significance.",
        "weaving": "Highlight loom techniques, thread types, cultural patterns, and historical use."
    }
    guideline = craft_guidelines.get(craft_type, "Describe the craft's unique techniques, materials, and cultural context in detail.")
    
    # Style consistency template
    style_template = f"Maintain a consistent {tone} tone throughout, using vivid, respectful language about artisans, including cultural details to enhance engagement and authenticity."
    
    # Explicit section requirements with examples
    section_example = """
    Example format:
    {
        "title": "Handmade Clay Pot of Timeless Craft",
        "narrative": "Originating from ancient villages, this pot is crafted using local clay by artisans honoring a 500-year tradition... (150-200 words)",
        "tutorial": "1. Prepare clay from local soil. 2. Shape on wheel with steady hands. 3. Fire in a wood kiln... (50-100 words, 3-5 steps)",
        "categories": ["pottery", "handmade", "traditional", "cultural heritage"]
    }
    """
    
    base_prompt = f"Create a detailed, culturally rich story about this {craft_type} craft image. {guideline} {style_template} {section_example} Return ONLY a JSON object with these keys: 'title' (5-10 words), 'narrative' (150-200 words about its creation with cultural context), 'tutorial' (50-100 words with 3-5 clear, culturally informed steps), 'categories' (list of 3-5 relevant categories including cultural aspects). Use {language} and ensure all keys are present with high quality or regenerate."
    return base_prompt