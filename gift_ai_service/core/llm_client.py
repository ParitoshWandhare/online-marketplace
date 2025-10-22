"""
🧠 Gemini LLM wrapper
"""

from google.generativeai import client as genai

def generate_text(model: str, prompt: str, max_output_tokens: int = 300):
    return genai.generate_text(
        model=model,
        prompt=prompt,
        max_output_tokens=max_output_tokens
    )
