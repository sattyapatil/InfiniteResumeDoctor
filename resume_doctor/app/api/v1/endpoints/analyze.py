"""
Resume Analysis Endpoints

Provides vitals check (free) and deep scan (premium) analysis endpoints
with tier-based rate limiting and file validation.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header, Request
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.gemini_service import analyze_with_gemini
from app.services.nlp_service import vitals_check
from app.core.auth import get_user_info, get_user_info_optional, check_tier_access
from app.core.config import settings
from app.core.rate_limits import (
    get_rate_limit_key,
    check_tier_access as check_rate_limit_access,
    get_tier_from_request,
    VITALS_GUEST_LIMIT,
    VITALS_FREE_LIMIT,
)

router = APIRouter()

# Get limiter from app state (will be set by main.py)
def get_limiter(request: Request) -> Limiter:
    return request.app.state.limiter


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded file is a valid PDF within size limits.
    Raises HTTPException if validation fails.
    """
    # Check content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid file type",
                "detail": "Only PDF files are supported",
                "content_type": file.content_type
            }
        )
    
    # Check file size (if available from headers)
    if file.size and file.size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "File too large",
                "detail": f"Maximum file size is {settings.MAX_FILE_SIZE_MB}MB",
                "file_size_mb": round(file.size / 1024 / 1024, 2),
                "max_size_mb": settings.MAX_FILE_SIZE_MB
            }
        )


async def read_and_validate_pdf(file: UploadFile) -> bytes:
    """
    Read PDF content and validate size after reading.
    Returns raw PDF bytes.
    """
    pdf_content = await file.read()
    
    # Validate size after reading (in case size wasn't in headers)
    if len(pdf_content) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "File too large",
                "detail": f"Maximum file size is {settings.MAX_FILE_SIZE_MB}MB",
                "file_size_mb": round(len(pdf_content) / 1024 / 1024, 2),
                "max_size_mb": settings.MAX_FILE_SIZE_MB
            }
        )
    
    if len(pdf_content) < 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "File too small",
                "detail": "File appears to be empty or corrupted"
            }
        )
    
    return pdf_content


@router.post("/vitals")
async def vitals_check_endpoint(
    request: Request,
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_tier: Optional[str] = Header(None)
):
    """
    Vitals Check - Available to all users (guest, free, paid)
    
    Performs lightweight local analysis of resume:
    - Readability score
    - Action verb analysis
    - Quantifiable metrics detection
    - Contact info validation
    
    Rate Limits (per 24 hours):
    - Guest: 3 requests
    - Free: 10 requests
    - Pro/Infinite: 20-100 requests
    """
    # Validate file
    validate_pdf_file(file)
    
    # Optional auth - guests can use this too
    user_data = get_user_info_optional(x_api_key, x_user_id, x_user_tier)
    tier = user_data.get("tier") if user_data else "guest"
    user_id = user_data.get("userId") if user_data else "guest"
    
    try:
        pdf_content = await read_and_validate_pdf(file)
        result = vitals_check(pdf_content)
        
        return {
            "type": "vitals",
            "result": result,
            "tier_required": "infinite-free",
            "user_tier": tier,
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Analysis failed",
                "detail": "Unable to process resume. Please try again."
            }
        )


@router.post("/deep-scan")
async def deep_scan_endpoint(
    request: Request,
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_tier: Optional[str] = Header(None)
):
    """
    Deep Scan - Requires Pro or Truly Infinite subscription
    
    AI-powered ATS analysis using Gemini:
    - Comprehensive scoring
    - Section-by-section feedback
    - Keyword gap analysis
    - Actionable recommendations
    
    Rate Limits (per 24 hours):
    - Pro: 10 requests
    - Truly Infinite: 50 requests
    """
    # Validate file
    validate_pdf_file(file)
    
    # Verify authentication (required for deep scan)
    user_data = get_user_info(x_api_key, x_user_id, x_user_tier)
    tier = user_data.get("tier", "infinite-free")
    
    # Check subscription tier
    if not check_tier_access(tier, ["infinite-pro", "truly-infinite"]):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Subscription required",
                "detail": "Deep Scan requires Pro or Truly Infinite subscription",
                "current_tier": tier,
                "required_tiers": ["infinite-pro", "truly-infinite"],
                "upgrade_url": "/pricing"
            }
        )
    
    try:
        pdf_content = await read_and_validate_pdf(file)
        result = analyze_with_gemini(pdf_content, job_description)
        
        return {
            "type": "deep_scan",
            "result": result,
            "tier_required": "infinite-pro",
            "user_tier": tier,
            "user_id": user_data.get("userId")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Deep scan failed",
                "detail": "AI analysis encountered an error. Please try again."
            }
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for analyze router"""
    return {
        "status": "healthy",
        "service": "Resume Doctor - Analysis",
        "endpoints": {
            "vitals": "POST /api/v1/analyze/vitals",
            "deep_scan": "POST /api/v1/analyze/deep-scan"
        },
        "config": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB
        }
    }

