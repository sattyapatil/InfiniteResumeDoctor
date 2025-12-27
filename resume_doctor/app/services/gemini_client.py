"""
Unified Gemini Client

Single source of truth for all Gemini AI interactions in the Resume Doctor service.
All services should use this client instead of directly importing genai.
"""

import google.generativeai as genai
import json
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings

# Configure Gemini once at module level
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiClient:
    """
    Unified Gemini AI client with consistent configuration and response handling.
    
    Usage:
        client = GeminiClient()
        result = client.generate_json(prompt)
        result = client.generate_json_with_pdf(pdf_bytes, prompt)
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize Gemini client with model from config (or override).
        
        Args:
            model_name: Optional override for model name. Defaults to config value.
        """
        self.model_name = model_name or settings.GEMINI_MODEL_NAME
        self._model = None
    
    @property
    def model(self) -> genai.GenerativeModel:
        """Lazy-load the Gemini model with JSON output config."""
        if self._model is None:
            self._model = genai.GenerativeModel(
                self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
        return self._model
    
    def clean_json_response(self, response_text: str) -> str:
        """
        Clean Gemini response to extract valid JSON.
        Handles markdown code blocks and extra whitespace.
        """
        text = response_text.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # Extract JSON object
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
        
        return text
    
    def generate_json(self, prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON response from text prompt.
        
        Args:
            prompt: The text prompt to send to Gemini
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            Exception: For API errors
        """
        response = self.model.generate_content(prompt)
        cleaned = self.clean_json_response(response.text)
        return json.loads(cleaned)
    
    def generate_json_with_pdf(
        self, 
        pdf_bytes: bytes, 
        prompt: str
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from PDF content + prompt.
        Uses Gemini's multimodal capability to process PDF directly.
        
        Args:
            pdf_bytes: Raw PDF file bytes
            prompt: The text prompt for analysis
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
            Exception: For API errors
        """
        response = self.model.generate_content([
            {'mime_type': 'application/pdf', 'data': pdf_bytes},
            prompt
        ])
        cleaned = self.clean_json_response(response.text)
        return json.loads(cleaned)
    
    def generate_json_with_content(
        self, 
        content_parts: List[Union[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from mixed content (text, images, PDFs).
        
        Args:
            content_parts: List of content parts - strings or dicts with mime_type/data
            
        Returns:
            Parsed JSON dictionary
        """
        response = self.model.generate_content(content_parts)
        cleaned = self.clean_json_response(response.text)
        return json.loads(cleaned)


# Default client instance (singleton pattern)
gemini_client = GeminiClient()
