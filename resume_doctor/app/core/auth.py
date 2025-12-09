import os
from typing import Optional
from fastapi import Header, HTTPException

# API Key for service-to-service authentication
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "your-secret-api-key-change-in-production")

def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """
    Verify API key from Builder app
    Simple validation that the request is coming from our own app
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_user_info(
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_tier: Optional[str] = Header(None)
) -> dict:
    """
    Get user information from headers
    Builder app passes tier and user ID directly
    """
    # Verify API key first
    verify_api_key(x_api_key)
    
    return {
        "userId": x_user_id or "guest",
        "tier": x_user_tier or "infinite-free"
    }

def get_user_info_optional(
    x_api_key: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_tier: Optional[str] = Header(None)
) -> Optional[dict]:
    """
    Get user info but don't require API key (for guest access)
    Returns None if no API key provided
    """
    if not x_api_key:
        return None
    
    try:
        verify_api_key(x_api_key)
        return {
            "userId": x_user_id or "guest",
            "tier": x_user_tier or "infinite-free"
        }
    except:
        return None

def check_tier_access(tier: str, required_tiers: list[str]) -> bool:
    """
    Check if user's tier allows access to a feature
    """
    return tier in required_tiers
