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
    - Leading/trailing whitespace and newlines
    - Extra text before/after JSON
    - Control characters
    """
    import re
    
    text = response_text.strip()
    
    # Log raw response for debugging (first 200 chars)
    print(f"[clean_json] Raw response (first 200 chars): {repr(text[:200])}")
    
    # Remove markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    # Try to find JSON object using regex (more robust)
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)
    else:
        # Fallback: find boundaries manually
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
    
    # Remove control characters that could break JSON parsing
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    print(f"[clean_json] Cleaned response (first 200 chars): {repr(text[:200])}")
    
    return text


# Gemini prompt for Vitals Check with sections and issues
VITALS_PROMPT = """You are a resume scoring expert. Analyze this resume and provide detailed feedback.

SCORING CRITERIA (0-100 each):
1. IMPACT (30% weight): Quantifiable achievements using %, $, numbers, metrics
2. BREVITY (20%): Concise bullet points (<2 lines), no long paragraphs
3. STYLE (20%): Active voice, strong action verbs (Led, Built, Drove, not "Responsible for")
4. COMPLETENESS (15%): Has contact info, summary/objective, experience, education, skills
5. ATS (15%): Standard section headers, keyword-rich, no graphics/tables mentioned

Calculate overall_score using the weighted formula.

IMPORTANT: Return ONLY valid JSON matching this exact structure:

{{"overall_score": 75, "impact_score": 70, "brevity_score": 80, "style_score": 75, "summary_feedback": "Strong technical skills. Needs more quantifiable achievements.", "experience_level": "mid", "industry": "technology", "sections": [{{"section_name": "Experience", "score": 70, "issues": ["Lacks quantifiable results", "Uses passive voice"], "actionable_fixes": ["Add metrics like revenue or efficiency %", "Start bullets with action verbs"]}}, {{"section_name": "Skills", "score": 85, "issues": ["Missing soft skills"], "actionable_fixes": ["Add leadership or communication skills"]}}], "missing_keywords": ["Python", "AWS", "Agile"]}}

RULES:
- overall_score = (impact*0.30 + brevity*0.20 + style*0.20 + completeness*0.15 + ats*0.15)
- experience_level: "entry" (<2 years), "mid" (2-7 years), "senior" (7+ years)
- industry: technology, finance, healthcare, marketing, education, legal, engineering, other
- summary_feedback: 1-2 sentences max, actionable
- sections: Analyze Experience, Education, Skills, Summary (2-4 sections max). Each needs score, issues array, actionable_fixes array.
- missing_keywords: 3-5 industry keywords the resume should include for ATS

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
    
    # Debug: Show extracted text
    print(f"[DEBUG] Extracted text (first 300 chars): {repr(text[:300] if text else 'NONE')}")
    
    # Need at least 200 chars for meaningful analysis
    if not text or len(text.strip()) < 200:
        print(f"[DEBUG] Text too short: {len(text.strip()) if text else 0} chars. Minimum: 200")
        return {
            "error": "Could not extract sufficient text from PDF",
            "overall_score": 0,
            "impact_score": 0,
            "brevity_score": 0,
            "style_score": 0,
            "summary_feedback": "Unable to read resume content. Please ensure the PDF is not image-based or encrypted.",
            "experience_level": "unknown",
            "industry": "unknown",
            "sections": [],
            "missing_keywords": [],
            "parsed_data": {},
            "extracted_text": text.strip() if text else ""
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
        
        print(f"[DEBUG] Resume text length: {len(text)}, truncated: {len(truncated_text)}", flush=True)
        
        prompt = VITALS_PROMPT.format(resume_text=truncated_text)
        
        print("[DEBUG] Calling Gemini API...", flush=True)
        response = model.generate_content(prompt)
        print("[DEBUG] Gemini API call complete", flush=True)
        
        # Debug: Print raw response
        print(f"[DEBUG] Raw Gemini response type: {type(response.text)}", flush=True)
        print(f"[DEBUG] Raw Gemini response (first 500 chars):\n{repr(response.text[:500])}", flush=True)
        
        # Clean the response to handle markdown/extra text
        cleaned_response = clean_json_response(response.text)
        print(f"[DEBUG] Cleaned response (first 500 chars):\n{repr(cleaned_response[:500])}", flush=True)
        
        # Try to parse JSON
        try:
            result = json.loads(cleaned_response)
            print(f"[DEBUG] JSON parsed successfully. Keys: {list(result.keys())}", flush=True)
        except json.JSONDecodeError as json_err:
            print(f"[DEBUG] JSON parse error: {json_err}", flush=True)
            print(f"[DEBUG] Error position: {json_err.pos}", flush=True)
            print(f"[DEBUG] Error line: {json_err.lineno}, col: {json_err.colno}", flush=True)
            print(f"[DEBUG] Problematic content around error: {repr(cleaned_response[max(0,json_err.pos-50):json_err.pos+50])}", flush=True)
            raise
        
        # Ensure all required fields exist with defaults
        return {
            "overall_score": result.get("overall_score", 50),
            "impact_score": result.get("impact_score", 50),
            "brevity_score": result.get("brevity_score", 50),
            "style_score": result.get("style_score", 50),
            "summary_feedback": result.get("summary_feedback", "Analysis complete."),
            "experience_level": result.get("experience_level", "mid"),
            "industry": result.get("industry", "other"),
            # Section-level feedback with issues
            "sections": result.get("sections", []),
            "missing_keywords": result.get("missing_keywords", []),
            "parsed_data": {},
            "extracted_text": text.strip()
        }
        
    except Exception as e:
        import traceback
        print(f"Gemini analysis error: {e}", flush=True)
        print(f"[DEBUG] Full traceback:\n{traceback.format_exc()}", flush=True)
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
            "parsed_data": {},
            "extracted_text": text.strip() if text else ""
        }


