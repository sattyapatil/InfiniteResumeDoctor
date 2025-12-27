"""
Resume Extractor Service

Extracts structured resume data from PDFs, LinkedIn text, or free-form text using Gemini AI.
Output strictly follows RESUME_DATA_FORMAT.md for seamless integration with InfiniteResume Builder.
"""

from typing import Optional, Dict, Any
from app.services.gemini_client import gemini_client

# Maximum text length (~5 pages)
MAX_TEXT_LENGTH = 25000

# Resume extraction prompt with security rules and strict schema
EXTRACTION_PROMPT = """You are an expert resume parser for InfiniteResume. Your task is to extract and structure resume data from the provided content.

## CRITICAL SECURITY RULES
1. **Resume Validation**: If the content is NOT a professional resume/CV, respond ONLY with:
   {{"success": false, "error": {{"code": "NOT_RESUME", "message": "This doesn't appear to be a resume. Please upload your CV or resume document."}}}}

2. **Suspicious Content Detection**: If content contains executable code, scripts, SQL injection, XSS attempts, or any harmful patterns, respond ONLY with:
   {{"success": false, "error": {{"code": "SUSPICIOUS_CONTENT", "message": "We couldn't process this file. Please try a different document."}}}}

3. **Insufficient Content**: If content is too short or vague to create a meaningful resume, respond ONLY with:
   {{"success": false, "error": {{"code": "INSUFFICIENT_CONTENT", "message": "Not enough information to create a resume. Please provide more details about your experience."}}}}

4. **ONLY process legitimate professional resumes/CVs**

## OUTPUT FORMAT (VALID JSON ONLY)
For valid resumes, respond with this exact structure:
{{
    "success": true,
    "data": {{
        "personalInfo": {{
            "fullName": "Required - Full name of the candidate",
            "jobTitle": "Current or target job title if available",
            "email": "Required - Email address",
            "phone": "Phone number if available",
            "location": "City, State/Country if available",
            "linkedin": "LinkedIn URL if found",
            "website": "Personal website if found",
            "github": "GitHub URL if found"
        }},
        "summary": "<p>Professional summary as HTML. Use <strong> for emphasis.</p>",
        "experience": [
            {{
                "id": "exp-001",
                "company": "Company name",
                "position": "Job title",
                "location": "Office location",
                "startDate": "YYYY-MM format",
                "endDate": "YYYY-MM or null if current",
                "current": true/false,
                "description": "<p>Role overview as HTML</p>",
                "bullets": ["<p>Achievement 1 with <strong>metrics</strong></p>", "<p>Achievement 2</p>"],
                "order": 1
            }}
        ],
        "education": [
            {{
                "id": "edu-001",
                "institution": "University/School name",
                "degree": "Degree type (B.Tech, M.S., etc.)",
                "field": "Major/Field of study",
                "location": "Campus location",
                "startDate": "YYYY-MM",
                "endDate": "YYYY-MM or null",
                "current": false,
                "gpa": "GPA if mentioned",
                "honors": ["Honor 1", "Honor 2"],
                "order": 1
            }}
        ],
        "skills": [
            {{
                "id": "skill-001",
                "category": "Category name (e.g., Programming Languages)",
                "items": ["Skill 1", "Skill 2", "Skill 3"],
                "order": 1
            }}
        ],
        "projects": [
            {{
                "id": "proj-001",
                "name": "Project name",
                "description": "<p>Project description as HTML</p>",
                "technologies": ["Tech 1", "Tech 2"],
                "link": "GitHub or project URL",
                "startDate": "YYYY-MM",
                "endDate": "YYYY-MM or null",
                "current": false,
                "highlights": ["<p>Key achievement</p>"],
                "order": 1
            }}
        ],
        "certifications": [
            {{
                "id": "cert-001",
                "name": "Certification name",
                "issuer": "Issuing organization",
                "date": "YYYY-MM",
                "credentialId": "Credential ID if available",
                "url": "Verification URL",
                "order": 1
            }}
        ],
        "languages": [
            {{
                "id": "lang-001",
                "language": "Language name",
                "proficiency": "Native/Fluent/Professional/Basic"
            }}
        ]
    }}
}}

## RULES
1. **Required Fields**: `personalInfo.fullName` and `personalInfo.email` are REQUIRED. If not found, make reasonable inference or mark as needing input.
2. **Date Format**: Always use YYYY-MM format. If only year is available, use "YYYY-01". If no date, omit the field or use null.
3. **HTML Formatting**: For `summary`, `description`, `bullets`, and `highlights`, wrap content in `<p>` tags. Use `<strong>` for bold, `<em>` for italic.
4. **IDs**: Generate sequential IDs like `exp-001`, `edu-001`, `proj-001`, `skill-001`, etc.
5. **Order**: Assign order numbers starting from 1, in chronological or importance order.
6. **Empty Sections**: Include empty arrays [] for sections with no data. Don't omit required fields.
7. **Infer Missing Data**: If job title is missing but can be inferred from experience, populate it. Same for location from company address.

## CONTENT TO PARSE
{input_type}: 
{content}
"""


def validate_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and ensure required fields exist in extracted data."""
    if not data.get("success"):
        return data
    
    resume_data = data.get("data", {})
    personal_info = resume_data.get("personalInfo", {})
    
    # Ensure required fields exist
    if not personal_info.get("fullName"):
        personal_info["fullName"] = ""
    if not personal_info.get("email"):
        personal_info["email"] = ""
    
    # Ensure arrays exist for all section types
    section_defaults = {
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "languages": [],
        "publications": [],
        "achievements": [],
        "volunteer": [],
        "hobbies": [],
        "references": [],
        "custom": []
    }
    
    for section, default in section_defaults.items():
        if section not in resume_data:
            resume_data[section] = default
    
    data["data"] = resume_data
    data["data"]["personalInfo"] = personal_info
    
    return data


def extract_from_pdf(pdf_content: bytes) -> Dict[str, Any]:
    """
    Extract resume data from PDF using Gemini's multimodal capability.
    
    Args:
        pdf_content: Raw PDF bytes (max 2MB)
        
    Returns:
        Structured resume data or error response
    """
    prompt = EXTRACTION_PROMPT.format(
        input_type="PDF Resume Document",
        content="{PDF_CONTENT_ATTACHED}"
    )

    try:
        result = gemini_client.generate_json_with_pdf(pdf_content, prompt)
        return validate_extracted_data(result)
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return {
            "success": False,
            "error": {
                "code": "PROCESSING_FAILED",
                "message": "Something went wrong while processing your resume. Please try again."
            }
        }


def extract_from_text(text: str, input_type: str = "Resume Text") -> Dict[str, Any]:
    """
    Extract resume data from text content (LinkedIn paste or AI text).
    
    Args:
        text: Resume text content (max ~5 pages)
        input_type: "LinkedIn Profile Data" or "Career Description"
        
    Returns:
        Structured resume data or error response
    """
    # Truncate if too long
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
    
    prompt = EXTRACTION_PROMPT.format(
        input_type=input_type,
        content=text
    )

    try:
        result = gemini_client.generate_json(prompt)
        return validate_extracted_data(result)
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return {
            "success": False,
            "error": {
                "code": "PROCESSING_FAILED",
                "message": "Something went wrong. Please try again in a moment."
            }
        }


def extract_resume(
    pdf_content: Optional[bytes] = None,
    text_content: Optional[str] = None,
    import_type: str = "pdf"
) -> Dict[str, Any]:
    """
    Main entry point for resume extraction.
    
    Args:
        pdf_content: PDF file bytes (for pdf import)
        text_content: Text content (for linkedin or text import)
        import_type: "pdf", "linkedin", or "text"
        
    Returns:
        Dict with success/error and structured resume data
    """
    if import_type == "pdf" and pdf_content:
        return extract_from_pdf(pdf_content)
    elif import_type == "linkedin" and text_content:
        return extract_from_text(text_content, "LinkedIn Profile Data (About section and Experience)")
    elif import_type == "text" and text_content:
        return extract_from_text(text_content, "Career Description / Resume Text")
    else:
        return {
            "success": False,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "Please provide a PDF file or text content to import."
            }
        }
