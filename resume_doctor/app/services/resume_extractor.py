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

## CONTENT VALIDATION RULES
1. **Suspicious Content Detection**: If content contains executable code, scripts, SQL injection, XSS attempts, or any harmful patterns, respond ONLY with:
   {{"success": false, "error": {{"code": "SUSPICIOUS_CONTENT", "message": "We couldn't process this content. Please try again with your resume information."}}}}

2. **Completely Unrelated Content**: ONLY reject if the content is completely unrelated to professional/career information (e.g., recipes, stories, random text). Respond with:
   {{"success": false, "error": {{"code": "NOT_RESUME", "message": "This doesn't seem to be career-related. Please describe your work experience or upload your resume."}}}}

3. **IMPORTANT - Be Generous with Career Descriptions**: If the input mentions ANY professional experience, job title, skills, education, or career information - even briefly - PROCESS IT and create a resume. The user is using our "AI Magic" feature to describe themselves.
   - If name/email is missing, use placeholders like "Your Name" and "your.email@example.com"
   - If dates are missing, omit them or use approximate dates
   - Infer and expand on the information provided
   - Be creative in structuring minimal input into resume sections

4. **Focus on Extraction**: Your primary goal is to HELP users create a resume, not to reject their input. Extract whatever professional information is available.

## OUTPUT FORMAT (VALID JSON ONLY)
For valid resumes, respond with this exact structure. ONLY include sections that have actual data - DO NOT include empty arrays or sections with no content:

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
        "summary": "<p>Professional summary as HTML. Use <strong> for emphasis. Can include paragraphs.</p>",
        "experience": [
            {{
                "id": "exp-001",
                "company": "Company name",
                "position": "Job title",
                "location": "Office location",
                "startDate": "YYYY-MM format",
                "endDate": "YYYY-MM or null if current",
                "current": true/false,
                "description": "<p>Role overview paragraph.</p><ul><li>Achievement 1 with <strong>metrics</strong></li><li>Achievement 2</li><li>Achievement 3</li></ul>",
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
                "description": "<p>Relevant coursework, thesis, or achievements.</p><ul><li>Honors: Dean's List</li><li>Activities: Student Government</li></ul>",
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
                "description": "<p>Project overview.</p><ul><li>Key feature or achievement</li><li>Technologies used impact</li></ul>",
                "technologies": ["Tech 1", "Tech 2"],
                "link": "GitHub or project URL",
                "startDate": "YYYY-MM",
                "endDate": "YYYY-MM or null",
                "current": false,
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

## CRITICAL RULES
1. **Required Fields**: `personalInfo.fullName` and `personalInfo.email` are REQUIRED. If not found, make reasonable inference or mark as needing input.
2. **Date Format**: Always use YYYY-MM format. If only year is available, use "YYYY-01". If no date, omit the field or use null.
3. **HTML Formatting**: For `summary`, `description` fields, use proper HTML:
   - Use `<p>` for paragraphs
   - Use `<ul><li>` for bullet points (achievements, highlights)
   - Use `<strong>` for bold emphasis (metrics, key achievements)
   - Use `<em>` for italic
   - Combine paragraphs and bullet lists in one `description` field
4. **IDs**: Generate sequential IDs like `exp-001`, `edu-001`, `proj-001`, `skill-001`, etc.
5. **Order**: Assign order numbers starting from 1, in chronological or importance order.
6. **OMIT EMPTY SECTIONS**: If a section has no data, DO NOT include it at all. No empty arrays.
7. **Infer Missing Data**: If job title is missing but can be inferred from experience, populate it. Same for location from company address.
8. **Experience Description**: Combine role overview AND achievements into ONE `description` field with paragraphs and bullet list.
9. **Do NOT include bullets field** - all bullet points go inside the description as `<ul><li>` HTML.

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
