# gift_ai_service/core/llm_client.py
"""
LLM Client - Unified interface for different LLM providers
Supports: Google Gemini, Anthropic Claude, OpenAI GPT
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("gift_ai.llm_client")

class LLMClient:
    """Unified LLM client with fallback support"""
    
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.genai = None
        self.anthropic = None
        self.openai = None
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers"""
        
        # Try Google Gemini first (preferred)
        if self.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.google_api_key)
                self.genai = genai
                logger.info("✅ Google Gemini initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
        
        # Try Anthropic Claude
        if self.anthropic_api_key:
            try:
                import anthropic
                self.anthropic = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("✅ Anthropic Claude initialized")
            except Exception as e:
                logger.warning(f"⚠️ Claude initialization failed: {e}")
        
        # Try OpenAI
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.openai = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
        
        if not any([self.genai, self.anthropic, self.openai]):
            logger.error("❌ No LLM providers available!")
    
    async def generate_text(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7,
        prefer_provider: Optional[str] = None
    ) -> str:
        """
        Generate text using available LLM provider
        
        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            prefer_provider: "gemini", "claude", or "openai" (optional)
        
        Returns:
            Generated text
        """
        
        # Try preferred provider first if specified
        if prefer_provider == "gemini" and self.genai:
            return await self._generate_gemini(prompt, max_tokens, temperature)
        elif prefer_provider == "claude" and self.anthropic:
            return await self._generate_claude(prompt, max_tokens, temperature)
        elif prefer_provider == "openai" and self.openai:
            return await self._generate_openai(prompt, max_tokens, temperature)
        
        # Default priority: Gemini -> Claude -> OpenAI
        if self.genai:
            return await self._generate_gemini(prompt, max_tokens, temperature)
        elif self.anthropic:
            return await self._generate_claude(prompt, max_tokens, temperature)
        elif self.openai:
            return await self._generate_openai(prompt, max_tokens, temperature)
        else:
            raise Exception("No LLM provider available")
    
    async def _generate_gemini(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Google Gemini"""
        try:
            model = self.genai.GenerativeModel('gemini-1.5-flash-001')
            response = model.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': max_tokens,
                    'temperature': temperature,
                }
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def _generate_claude(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using Anthropic Claude"""
        try:
            message = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            raise
    
    async def _generate_openai(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using OpenAI"""
        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def get_available_providers(self) -> list[str]:
        """Get list of available LLM providers"""
        providers = []
        if self.genai:
            providers.append("gemini")
        if self.anthropic:
            providers.append("claude")
        if self.openai:
            providers.append("openai")
        return providers
    
    def is_available(self) -> bool:
        """Check if any LLM provider is available"""
        return any([self.genai, self.anthropic, self.openai])