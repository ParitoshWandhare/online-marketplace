"""
llm_client.py
-------------
Provides a lightweight wrapper for calling an LLM (like OpenAI).
Supports simple text generation and embedding generation used in
the Gift AI pipeline.
"""

import os
from typing import Optional, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """
    Handles communication with OpenAI API (or any future LLM backend).

    Usage:
        llm = LLMClient()
        text = llm.generate_text("Suggest Diwali gifts for parents")
        embedding = llm.get_embedding("Handmade Diwali diya")
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in environment variables.")
        self.client = OpenAI(api_key=api_key)

    def generate_text(self, prompt: str, max_tokens: int = 300) -> str:
        """
        Generates creative text suggestions using an OpenAI model.
        """
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative gift recommendation assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding vector for semantic search / similarity.
        """
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
