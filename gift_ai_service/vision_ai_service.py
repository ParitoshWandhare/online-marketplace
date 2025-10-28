"""
Vision AI Service - Gemini Vision Only Implementation
Supports: Gemini Vision with Ollama LLaVA fallback
Port: 8004
"""

import os
import io
import logging
import base64
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import google.generativeai as genai

# ========================================================================
# LOAD ENVIRONMENT VARIABLES
# ========================================================================
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================================================
# FASTAPI APP
# ========================================================================
app = FastAPI(
    title="Vision AI Service",
    description="Vision AI endpoints using Gemini Vision",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# VISION AI CLIENT INITIALIZATION (GEMINI ONLY)
# ========================================================================
class VisionAIClient:
    """Gemini Vision AI client with Ollama fallback"""
    
    def __init__(self):
        # Load Gemini API key (try both env variable names)
        self.gemini_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        # Debug: Print API key status
        if self.gemini_api_key:
            logger.info(f"🔑 Gemini API Key loaded: {self.gemini_api_key[:10]}...")
        else:
            logger.error("❌ GEMINI_API_KEY not found in environment!")
        
        # Initialize Gemini Vision
        self.gemini_model = None
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                
                # List available models to find the right one
                logger.info("📋 Checking available Gemini models...")
                available_models = []
                
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            available_models.append(m.name)
                            logger.info(f"  ✓ {m.name}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not list models: {e}")
                
                # Try different model names in order of preference (based on your available models)
                model_names = [
                    'gemini-2.5-flash',              # Fast and efficient (recommended)
                    'gemini-2.0-flash',              # Stable version
                    'gemini-pro-latest',             # Latest stable pro
                    'gemini-flash-latest',           # Latest flash
                    'gemini-2.5-pro',                # Most capable
                    'gemini-2.0-flash-001',          # Specific version
                    'models/gemini-2.5-flash',       # With models/ prefix
                    'models/gemini-2.0-flash',
                    'models/gemini-pro-latest'
                ]
                
                for model_name in model_names:
                    try:
                        self.gemini_model = genai.GenerativeModel(model_name)
                        # Test the model with a simple call
                        logger.info(f"✅ Gemini Vision initialized with: {model_name}")
                        break
                    except Exception as e:
                        logger.debug(f"⚠️ Failed to init {model_name}: {e}")
                        continue
                
                if not self.gemini_model:
                    logger.error(f"❌ No suitable Gemini model found.")
                    if available_models:
                        logger.error(f"Available models: {available_models}")
                    
            except Exception as e:
                self.gemini_model = None
                logger.error(f"❌ Gemini initialization failed: {e}")
        else:
            logger.warning("⚠️ Gemini API key not found")
        
        # Check for local Ollama LLaVA as fallback
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama with LLaVA is available"""
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                has_llava = any('llava' in m.get('name', '').lower() for m in models)
                if has_llava:
                    logger.info("✅ Ollama LLaVA available as fallback")
                    return True
        except Exception as e:
            logger.debug(f"Ollama check failed: {e}")
            pass
        logger.info("ℹ️ Ollama LLaVA not available (optional fallback)")
        return False
    
    async def analyze_image_gemini(self, image_bytes: bytes, prompt: str) -> str:
        """Analyze image using Gemini Vision"""
        if not self.gemini_model:
            raise Exception("Gemini not configured")
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Generate response
            response = self.gemini_model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            raise
    
    async def analyze_image_ollama(self, image_bytes: bytes, prompt: str) -> str:
        """Analyze image using local Ollama LLaVA"""
        if not self.ollama_available:
            raise Exception("Ollama LLaVA not available")
        
        try:
            import requests
            
            # Encode image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llava',
                    'prompt': prompt,
                    'images': [base64_image],
                    'stream': False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama error: {response.status_code}")
        except Exception as e:
            logger.error(f"Ollama Vision error: {e}")
            raise
    
    async def analyze_image(self, image_bytes: bytes, prompt: str) -> str:
        """
        Analyze image with fallback chain:
        Gemini → Ollama → Error
        """
        # Try Gemini first
        if self.gemini_model:
            try:
                return await self.analyze_image_gemini(image_bytes, prompt)
            except Exception as e:
                logger.warning(f"Gemini failed: {e}, trying Ollama fallback...")
        
        # Try Ollama as fallback
        if self.ollama_available:
            try:
                return await self.analyze_image_ollama(image_bytes, prompt)
            except Exception as e:
                logger.error(f"Ollama fallback also failed: {e}")
        
        raise Exception("No vision AI provider available. Please check your Gemini API key.")

# Initialize global client
vision_client = VisionAIClient()

# ========================================================================
# HELPER: Parse JSON from LLM response
# ========================================================================
def extract_json_from_response(text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response (handles markdown blocks)"""
    import json
    import re
    
    # Try to find JSON block
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find any JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: extract key-value pairs manually
        logger.warning("Failed to parse JSON, using fallback parsing")
        return {"raw_response": text}

# ========================================================================
# VISION AI ENDPOINTS
# ========================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "gemini_available": vision_client.gemini_model is not None,
        "ollama_available": vision_client.ollama_available
    }

@app.post("/analyze_craft")
async def analyze_craft(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Detect craft type (pottery, textile, metalwork, painting, etc.)
    Uses: Gemini Vision
    """
    logger.info(f"🎨 Analyzing craft in {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze this image and identify the type of craft or artwork shown.
        
Return a JSON object with:
{
    "craft_type": "pottery|textile|metalwork|painting|sculpture|woodwork|jewelry|other",
    "confidence": 0.0-1.0,
    "details": "brief description"
}

Focus on identifying the primary craft category."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        # Ensure required fields
        result.setdefault('craft_type', 'unknown')
        result.setdefault('confidence', 0.5)
        
        logger.info(f"✅ Craft detected: {result.get('craft_type')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Craft analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/analyze_quality")
async def analyze_quality(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Assess craftsmanship quality
    """
    logger.info(f"🔍 Analyzing quality of {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze the quality and craftsmanship of this item.

Return JSON:
{
    "quality": "high|medium|low",
    "details": "describe finish, craftsmanship, flaws",
    "craftsmanship_score": 0.0-1.0
}

Look for: surface finish, symmetry, attention to detail, defects."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('quality', 'medium')
        result.setdefault('details', 'No details available')
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/estimate_price")
async def estimate_price(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Estimate price range based on visual analysis
    """
    logger.info(f"💰 Estimating price for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Estimate the price range for this handmade item in Indian Rupees (₹).

Return JSON:
{
    "price_range_inr": "₹min-₹max",
    "estimated_price": numeric_value,
    "method": "description of estimation basis",
    "factors": ["factor1", "factor2"]
}

Consider: material quality, craftsmanship, size (apparent), complexity, market standards."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('price_range_inr', '₹500-1500')
        result.setdefault('method', 'visual estimation')
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Price estimation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_fraud")
async def detect_fraud(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Detect potential fraud indicators
    """
    logger.info(f"🚨 Fraud detection for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze this image for potential fraud indicators.

Return JSON:
{
    "fraud_score": 0.0-1.0,
    "is_suspicious": true|false,
    "red_flags": ["flag1", "flag2"],
    "authenticity_indicators": ["indicator1"]
}

Check for: stock photo watermarks, inconsistent quality, AI-generated features, 
duplicate listings, professional staging vs actual handmade."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('fraud_score', 0.0)
        result.setdefault('is_suspicious', False)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Fraud detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/suggest_packaging")
async def suggest_packaging(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Recommend appropriate packaging
    """
    logger.info(f"📦 Packaging suggestions for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Recommend packaging for this item.

Return JSON:
{
    "packaging": "description of recommended packaging",
    "cost": estimated_cost_in_rupees,
    "materials": ["material1", "material2"],
    "special_requirements": ["requirement1"]
}

Consider: fragility, size, eco-friendliness, gift presentation."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('packaging', 'standard eco-friendly box')
        result.setdefault('cost', 100)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Packaging suggestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_material")
async def detect_material(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Identify materials used
    """
    logger.info(f"🔬 Material detection for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Identify the materials used in this item.

Return JSON:
{
    "material": "primary material name",
    "purity": 0.0-1.0,
    "additional_materials": ["material1", "material2"],
    "texture": "description"
}

Analyze: visual texture, color, reflectivity, surface characteristics."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('material', 'unknown')
        result.setdefault('purity', 0.8)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Material detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_sentiment")
async def analyze_sentiment(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Analyze emotional sentiment and aesthetic appeal
    """
    logger.info(f"❤️ Sentiment analysis for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Analyze the emotional sentiment and aesthetic appeal of this item.

Return JSON:
{
    "sentiment": "warm|playful|elegant|traditional|modern|rustic",
    "emotion": "joyful|peaceful|energetic|nostalgic|sophisticated",
    "appeal_score": 0.0-1.0,
    "target_audience": "description"
}

Consider: color palette, design style, cultural elements, intended mood."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('sentiment', 'neutral')
        result.setdefault('emotion', 'pleasant')
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_occasion")
async def detect_occasion(image: UploadFile = File(...)) -> Dict:
    """
    Vision AI: Detect suitable occasions for gifting
    """
    logger.info(f"🎉 Occasion detection for {image.filename}")
    
    try:
        image_bytes = await image.read()
        
        prompt = """Identify suitable occasions for gifting this item.

Return JSON:
{
    "occasion": "primary occasion (birthday|wedding|diwali|housewarming|anniversary|general)",
    "confidence": 0.0-1.0,
    "suitable_occasions": ["occasion1", "occasion2"],
    "cultural_significance": "if any"
}

Consider: cultural symbols, design elements, traditional vs modern style."""
        
        response = await vision_client.analyze_image(image_bytes, prompt)
        result = extract_json_from_response(response)
        
        result.setdefault('occasion', 'general')
        result.setdefault('confidence', 0.7)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Occasion detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================================================
# RUN SERVER
# ========================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "vision_ai_service:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    )