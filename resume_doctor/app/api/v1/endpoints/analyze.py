from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from typing import Optional
from app.services.gemini_service import analyze_with_gemini
from app.services.nlp_service import vitals_check
from app.core.auth import get_user_info, get_user_info_optional, check_tier_access

router = APIRouter()

@router.post("/vitals")
async def vitals_check_endpoint(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_tier: Optional[str] = Header(None)
):
    """
    Vitals Check - Available to all users (guest, free, paid)
    Frontend-based basic completeness check
    No authentication required, but we track usage if authenticated
    """
    # Optional auth - guests can use this too
    user_data = get_user_info_optional(x_api_key, x_user_id, x_user_tier)
    
    try:
        pdf_content = await file.read()
        result = vitals_check(pdf_content)
        
        return {
            "type": "vitals",
            "result": result,
            "tier_required": "infinite-free",
            "user_tier": user_data.get("tier") if user_data else "guest",
            "user_id": user_data.get("userId") if user_data else "guest"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/deep-scan")
async def deep_scan_endpoint(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_tier: Optional[str] = Header(None)
):
    """
    Deep Scan - Requires Pro or Truly Infinite subscription
    AI-powered ATS analysis using Gemini
    """
    # Verify authentication (required for deep scan)
    user_data = get_user_info(x_api_key, x_user_id, x_user_tier)
    tier = user_data.get("tier", "infinite-free")
    
    # Check subscription tier
    if not check_tier_access(tier, ["infinite-pro", "truly-infinite"]):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Deep Scan requires Pro or Truly Infinite subscription",
                "current_tier": tier,
                "required_tiers": ["infinite-pro", "truly-infinite"],
                "upgrade_url": "/pricing"
            }
        )
    
    try:
        pdf_content = await file.read()
        result = analyze_with_gemini(pdf_content, job_description)
        
        return {
            "type": "deep_scan",
            "result": result,
            "tier_required": "infinite-pro",
            "user_tier": tier,
            "user_id": user_data.get("userId")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deep scan failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Resume Doctor",
        "endpoints": {
            "vitals": "POST /api/v1/analyze/vitals",
            "deep_scan": "POST /api/v1/analyze/deep-scan"
        }
    }
