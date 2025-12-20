"""
Resume Text Extraction and Vitals Check Service

Lightweight service using:
- pdfminer.six for PDF text extraction (best accuracy for complex layouts)
- Gemini Flash-Lite for quick resume scoring (minimal tokens)

No heavy local NLP dependencies (textstat, nltk removed for Railway optimization).
"""

import io
import json
import google.generativeai as genai
from pdfminer.high_level import extract_text
from app.core.config import settings

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from a PDF file using pdfminer.six.
    Handles multi-column resume layouts better than pypdf.
    
    Args:
        file_content: Raw PDF bytes
        
    Returns:
        Extracted text string
    """
    try:
        text = extract_text(io.BytesIO(file_content))
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def clean_json_response(response_text: str) -> str:
    """
    Clean Gemini response to extract valid JSON.
    Handles common issues:
    - Markdown code blocks (```json ... ```)
    - Leading/trailing whitespace
    - Extra text before/after JSON
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
    
    # Find JSON object boundaries
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        text = text[start_idx:end_idx + 1]
    
    return text


# Lightweight Gemini prompt for Vitals Check (~500 tokens)
VITALS_PROMPT = """You are a resume scoring expert. Analyze this resume and provide scores.

SCORING CRITERIA (0-100 each):
1. IMPACT (30% weight): Quantifiable achievements using %, $, numbers, metrics
2. BREVITY (20%): Concise bullet points (<2 lines), no long paragraphs
3. STYLE (20%): Active voice, strong action verbs (Led, Built, Drove, not "Responsible for")
4. COMPLETENESS (15%): Has contact info, summary/objective, experience, education, skills
5. ATS (15%): Standard section headers, keyword-rich, no graphics/tables mentioned

Calculate overall_score using the weighted formula.

IMPORTANT: Return ONLY valid JSON, no markdown, no code blocks, no explanation.

{"overall_score": 75, "impact_score": 70, "brevity_score": 80, "style_score": 75, "summary_feedback": "Strong technical skills. Needs more quantifiable achievements.", "experience_level": "mid", "industry": "technology"}

RULES:
- overall_score = (impact*0.30 + brevity*0.20 + style*0.20 + completeness*0.15 + ats*0.15)
- experience_level: "entry" (<2 years), "mid" (2-7 years), "senior" (7+ years)
- industry: technology, finance, healthcare, marketing, education, legal, engineering, other
- summary_feedback: 1-2 sentences max, actionable

RESUME TEXT:
{resume_text}
"""


def vitals_check(pdf_content: bytes) -> dict:
    """
    Main entry point for Vitals Check (Free Tier).
    Uses Gemini Flash-Lite for fast, accurate scoring.
    
    Args:
        pdf_content: Raw PDF file bytes
        
    Returns:
        Dictionary with scores and summary:
        - overall_score (0-100)
        - impact_score (0-100)
        - brevity_score (0-100)
        - style_score (0-100)
        - summary_feedback (string)
        - experience_level (entry/mid/senior)
        - industry (string)
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_content)
    
    if not text or len(text.strip()) < 50:
        return {
            "error": "Could not extract sufficient text from PDF",
            "overall_score": 0,
            "impact_score": 0,
            "brevity_score": 0,
            "style_score": 0,
            "summary_feedback": "Unable to read resume content. Please ensure the PDF is not image-based or encrypted.",
            "experience_level": "unknown",
            "industry": "unknown"
        }
    
    try:
        # Use lightweight Gemini model for quick scoring
        model = genai.GenerativeModel(
            'gemini-2.0-flash-lite',
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Truncate text if too long (save tokens)
        max_chars = 8000  # ~2000 tokens
        truncated_text = text[:max_chars] if len(text) > max_chars else text
        
        prompt = VITALS_PROMPT.format(resume_text=truncated_text)
        
        response = model.generate_content(prompt)
        
        # Clean the response to handle markdown/extra text
        cleaned_response = clean_json_response(response.text)
        result = json.loads(cleaned_response)
        
        # Ensure all required fields exist with defaults
        return {
            "overall_score": result.get("overall_score", 50),
            "impact_score": result.get("impact_score", 50),
            "brevity_score": result.get("brevity_score", 50),
            "style_score": result.get("style_score", 50),
            "summary_feedback": result.get("summary_feedback", "Analysis complete."),
            "experience_level": result.get("experience_level", "mid"),
            "industry": result.get("industry", "other"),
            # Placeholder fields for UI compatibility
            "sections": [],
            "missing_keywords": [],
            "parsed_data": {}
        }
        
    except Exception as e:
        print(f"Gemini analysis error: {e}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "overall_score": 0,
            "impact_score": 0,
            "brevity_score": 0,
            "style_score": 0,
            "summary_feedback": "Analysis service encountered an error. Please try again.",
            "experience_level": "unknown",
            "industry": "unknown",
            "sections": [],
            "missing_keywords": [],
            "parsed_data": {}
        }


