import google.generativeai as genai
import os
import json
from app.core.config import settings
from app.schemas.resume import AnalysisResult

genai.configure(api_key=settings.GEMINI_API_KEY)

def analyze_with_gemini(pdf_content: bytes, job_description: str = None) -> str:
    model = genai.GenerativeModel(
        'gemini-2.0-flash-lite',
        generation_config={"response_mime_type": "application/json"}
    )

    prompt = """
    You are an expert ATS Resume Auditor. 
    Analyze the attached resume PDF. 
    If a Job Description is provided, compare the resume against it.
    
    CRITICAL: Return the response strictly in this JSON schema:
    {
        "overall_score": int,
        "summary_feedback": "2 sentences max summary",
        "impact_score": int,
        "brevity_score": int,
        "style_score": int,
        "sections": [
            {
                "section_name": "Experience",
                "score": int,
                "issues": ["bullet point 1 is vague", "passive voice used"],
                "actionable_fixes": ["Use 'Spearheaded' instead of 'Led'", "Add metrics to point 2"]
            }
        ],
        "missing_keywords": ["Python", "AWS"],
        "parsed_data": { 
            "full_name": "...", 
            "email": "...",
            "skills": ["..."],
            "experience": [...] 
        }
    }
    
    Scoring Rules:
    - Impact Score: High if resume uses numbers (%, $) to prove results.
    - Brevity Score: High if bullet points are concise (not paragraphs).
    - Style Score: High if active voice and strong grammar are used.
    """
    
    if job_description:
        prompt += f"\n\nJob Description:\n{job_description}"
    
    # Gemini 1.5 can take raw PDF bytes as input part
    # We need to wrap the bytes in a way Gemini expects, usually as a Part object or similar
    # For simplicity with the python SDK, we can pass the bytes directly if supported or use a Blob
    
    response = model.generate_content([
        {'mime_type': 'application/pdf', 'data': pdf_content},
        prompt
    ])
    
    return response.text # Returns JSON string
