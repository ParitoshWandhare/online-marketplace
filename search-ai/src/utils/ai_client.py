import google.generativeai as genai
from src.config.settings import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
