"""
Rate Limiting Configuration for Resume Doctor API

Implements tiered rate limiting based on user subscription tier.
All limits use a 24-hour sliding window to align with Pro tier validity.
"""

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional, Callable

# Tier-based rate limit configuration (per 24-hour window)
TIER_RATE_LIMITS = {
    # Guest users (no account) - IP-based limiting
    "guest": {
        "vitals": "3/day",      # Basic bot protection
        "deep_scan": None,      # Not allowed
    },
    # Free tier users - User ID-based limiting
    "infinite-free": {
        "vitals": "10/day",     # Fair usage
        "deep_scan": None,      # Not allowed
    },
    # Pro tier users (24-hour access)
    "infinite-pro": {
        "vitals": "20/day",     # ~$0.015 AI cost
        "deep_scan": "10/day",  # Premium feature
    },
    # Truly Infinite users (90-day access)
    "truly-infinite": {
        "vitals": "100/day",    # Generous limit
        "deep_scan": "50/day",  # ~$0.075 AI cost
    },
}

def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on user identity.
    Uses user ID for authenticated users, IP for guests.
    """
    user_id = request.headers.get("X-User-Id")
    
    # Authenticated user with valid ID
    if user_id and user_id != "guest":
        return f"user:{user_id}"
    
    # Fall back to IP-based limiting for guests
    return f"ip:{get_remote_address(request)}"


def get_tier_from_request(request: Request) -> str:
    """Extract user tier from request headers"""
    tier = request.headers.get("X-User-Tier", "guest")
    
    # Validate tier is recognized
    if tier not in TIER_RATE_LIMITS:
        return "guest"
    
    return tier


def get_rate_limit_for_tier(tier: str, endpoint: str) -> Optional[str]:
    """
    Get the rate limit string for a given tier and endpoint.
    Returns None if the endpoint is blocked for that tier.
    """
    tier_limits = TIER_RATE_LIMITS.get(tier, TIER_RATE_LIMITS["guest"])
    return tier_limits.get(endpoint)


def check_tier_access(tier: str, endpoint: str) -> bool:
    """
    Check if a tier has access to an endpoint.
    Returns False if rate limit is None (blocked).
    """
    limit = get_rate_limit_for_tier(tier, endpoint)
    return limit is not None


def create_dynamic_limiter() -> Limiter:
    """Create a limiter with dynamic key function"""
    return Limiter(key_func=get_rate_limit_key)


# Pre-configured rate limit strings for decorator use
VITALS_GUEST_LIMIT = "3/day"
VITALS_FREE_LIMIT = "10/day"
VITALS_PRO_LIMIT = "20/day"
VITALS_INFINITE_LIMIT = "100/day"

DEEP_SCAN_PRO_LIMIT = "10/day"
DEEP_SCAN_INFINITE_LIMIT = "50/day"


def rate_limit_exceeded_handler(request: Request, exc: Exception):
    """
    Custom handler for rate limit exceeded errors.
    Returns a user-friendly response with Retry-After header.
    """
    from fastapi.responses import JSONResponse
    
    # Calculate retry time (simplified - 1 hour for safety)
    retry_after = 3600
    
    tier = get_tier_from_request(request)
    
    response_data = {
        "error": "Rate limit exceeded",
        "detail": "You have exceeded the maximum number of requests. Please try again later.",
        "tier": tier,
        "retry_after_seconds": retry_after,
    }
    
    # Add upgrade suggestion for non-premium tiers
    if tier in ["guest", "infinite-free"]:
        response_data["upgrade_hint"] = "Upgrade to Pro for higher limits"
    
    return JSONResponse(
        status_code=429,
        content=response_data,
        headers={"Retry-After": str(retry_after)}
    )
