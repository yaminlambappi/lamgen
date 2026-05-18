import os
import google.generativeai as genai
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_gemini_provider() -> Optional[Any]:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY is not set in environment.")
        return None
    
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    return genai.GenerativeModel(model_name)

def generate_ai_response(prompt: str, max_retries: int = 3, timeout: int = 30) -> str:
    """Centralized AI execution with Gemini."""
    model = get_gemini_provider()
    if not model:
        raise Exception("AI Provider not configured.")
        
    for attempt in range(max_retries):
        try:
            # We don't have explicit timeout on generate_content in the library often, 
            # but we can rely on standard timeouts or requests timeout if available.
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.warning(f"AI Generation failed attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error("AI Generation failed completely.")
                raise e
    return ""
