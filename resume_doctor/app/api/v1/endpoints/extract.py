"""
Resume Extract Endpoint

API endpoint for extracting structured resume data from PDFs or text.
Includes file validation, size limits, and security checks.
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.services.resume_extractor import extract_resume
from app.core.config import settings

router = APIRouter()

# Maximum file size: 2MB
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# PDF magic bytes signature
PDF_MAGIC = b"%PDF"


def validate_pdf_file(file_content: bytes) -> tuple[bool, str]:
    """
    Validate that the uploaded file is a legitimate PDF.
    Uses pure Python magic byte checking - no system dependencies.
    
    Returns:
        tuple of (is_valid, error_message)
    """
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        return False, "Your file is too large (max 2MB). Try compressing the PDF or removing images."
    
    # Check if content is empty
    if len(file_content) < 10:
        return False, "The file appears to be empty or corrupted."
    
    # Check PDF magic bytes (PDF signature: %PDF-x.x)
    if not file_content[:4].startswith(PDF_MAGIC):
        return False, "Please upload a PDF file. Other formats aren't supported yet."
    
    return True, ""


@router.post("/pdf")
async def extract_from_pdf_endpoint(
    file: UploadFile = File(...),
):
    """
    Extract resume data from uploaded PDF file.
    
    - **file**: PDF file (max 2MB)
    
    Returns structured resume data matching RESUME_DATA_FORMAT.md
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file
        is_valid, error_message = validate_pdf_file(file_content)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "code": "INVALID_FILE",
                        "message": error_message
                    }
                }
            )
        
        # Extract resume data using Gemini
        result = extract_resume(pdf_content=file_content, import_type="pdf")
        
        if result.get("success"):
            return JSONResponse(content=result)
        else:
            return JSONResponse(
                status_code=422,
                content=result
            )
            
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "PROCESSING_FAILED",
                    "message": "Something went wrong. Please try again in a moment."
                }
            }
        )


@router.post("/text")
async def extract_from_text_endpoint(
    text: str = Form(...),
    import_type: str = Form("text")  # "linkedin" or "text"
):
    """
    Extract resume data from text content.
    
    - **text**: Resume text or LinkedIn profile data (max ~5 pages)
    - **import_type**: "linkedin" for LinkedIn data, "text" for general text
    
    Returns structured resume data matching RESUME_DATA_FORMAT.md
    """
    # Validate text length
    MAX_TEXT_LENGTH = 25000  # ~5 pages
    MIN_TEXT_LENGTH = 50
    
    if len(text) < MIN_TEXT_LENGTH:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "INSUFFICIENT_CONTENT",
                    "message": "The content is too short. Please provide more details about your experience."
                }
            }
        )
    
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
    
    # Validate import type
    if import_type not in ["linkedin", "text"]:
        import_type = "text"
    
    try:
        # Extract resume data using Gemini
        result = extract_resume(text_content=text, import_type=import_type)
        
        if result.get("success"):
            return JSONResponse(content=result)
        else:
            return JSONResponse(
                status_code=422,
                content=result
            )
            
    except Exception as e:
        print(f"Text extraction error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "PROCESSING_FAILED",
                    "message": "Something went wrong. Please try again in a moment."
                }
            }
        )
