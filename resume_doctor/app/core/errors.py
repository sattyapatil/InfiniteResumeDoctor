"""
User-Friendly Error Messages for Resume Doctor API

Maps internal error codes to user-facing messages.
System errors are hidden from users to prevent security exposure.
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass


class ErrorCode(str, Enum):
    """Standardized error codes for Resume Doctor API"""
    
    # File Validation Errors (400)
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_TOO_SMALL = "FILE_TOO_SMALL"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    
    # Authentication Errors (401)
    AUTH_REQUIRED = "AUTH_REQUIRED"
    INVALID_API_KEY = "INVALID_API_KEY"
    
    # Authorization Errors (403)
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"
    FEATURE_LOCKED = "FEATURE_LOCKED"
    
    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    DAILY_QUOTA_EXCEEDED = "DAILY_QUOTA_EXCEEDED"
    
    # Processing Errors (500)
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    PDF_EXTRACTION_FAILED = "PDF_EXTRACTION_FAILED"
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class UserFriendlyError:
    """User-friendly error with actionable message"""
    code: ErrorCode
    status_code: int
    title: str
    message: str
    action: Optional[str] = None  # What user can do
    upgrade_url: Optional[str] = None  # For subscription errors
    retry_after: Optional[int] = None  # For rate limit errors


# User-friendly error messages (no technical details exposed)
ERROR_MESSAGES: Dict[ErrorCode, UserFriendlyError] = {
    # File Validation
    ErrorCode.INVALID_FILE_TYPE: UserFriendlyError(
        code=ErrorCode.INVALID_FILE_TYPE,
        status_code=400,
        title="Invalid File Type",
        message="Please upload a PDF file. Other formats are not supported.",
        action="Convert your resume to PDF format and try again."
    ),
    ErrorCode.FILE_TOO_LARGE: UserFriendlyError(
        code=ErrorCode.FILE_TOO_LARGE,
        status_code=400,
        title="File Too Large",
        message="Your resume file exceeds the 5MB limit.",
        action="Compress your PDF or remove embedded images to reduce file size."
    ),
    ErrorCode.FILE_TOO_SMALL: UserFriendlyError(
        code=ErrorCode.FILE_TOO_SMALL,
        status_code=400,
        title="Empty File",
        message="The uploaded file appears to be empty or corrupted.",
        action="Please upload a valid PDF resume."
    ),
    ErrorCode.FILE_CORRUPTED: UserFriendlyError(
        code=ErrorCode.FILE_CORRUPTED,
        status_code=400,
        title="Unable to Read File",
        message="We couldn't read the content of your resume.",
        action="Make sure your PDF is not password-protected or corrupted."
    ),
    
    # Authentication
    ErrorCode.AUTH_REQUIRED: UserFriendlyError(
        code=ErrorCode.AUTH_REQUIRED,
        status_code=401,
        title="Sign In Required",
        message="Please sign in to use this feature.",
        action="Create a free account to get started."
    ),
    ErrorCode.INVALID_API_KEY: UserFriendlyError(
        code=ErrorCode.INVALID_API_KEY,
        status_code=401,
        title="Session Expired",
        message="Your session has expired.",
        action="Please refresh the page and try again."
    ),
    
    # Authorization
    ErrorCode.SUBSCRIPTION_REQUIRED: UserFriendlyError(
        code=ErrorCode.SUBSCRIPTION_REQUIRED,
        status_code=403,
        title="Pro Feature",
        message="Deep Scan is a Pro feature. Upgrade to unlock comprehensive AI analysis.",
        action="Upgrade now to get detailed feedback on every section of your resume.",
        upgrade_url="/pricing"
    ),
    ErrorCode.FEATURE_LOCKED: UserFriendlyError(
        code=ErrorCode.FEATURE_LOCKED,
        status_code=403,
        title="Feature Locked",
        message="This feature is not available on your current plan.",
        action="Upgrade to access all features.",
        upgrade_url="/pricing"
    ),
    
    # Rate Limiting
    ErrorCode.RATE_LIMIT_EXCEEDED: UserFriendlyError(
        code=ErrorCode.RATE_LIMIT_EXCEEDED,
        status_code=429,
        title="Slow Down",
        message="You're sending requests too quickly.",
        action="Please wait a moment before trying again.",
        retry_after=60
    ),
    ErrorCode.DAILY_QUOTA_EXCEEDED: UserFriendlyError(
        code=ErrorCode.DAILY_QUOTA_EXCEEDED,
        status_code=429,
        title="Daily Limit Reached",
        message="You've used all your resume scans for today.",
        action="Upgrade to Pro for more daily scans, or try again tomorrow.",
        upgrade_url="/pricing",
        retry_after=86400  # 24 hours
    ),
    
    # Processing Errors (hide technical details)
    ErrorCode.ANALYSIS_FAILED: UserFriendlyError(
        code=ErrorCode.ANALYSIS_FAILED,
        status_code=500,
        title="Analysis Failed",
        message="Something went wrong while analyzing your resume.",
        action="Please try again. If the problem persists, try a different PDF."
    ),
    ErrorCode.PDF_EXTRACTION_FAILED: UserFriendlyError(
        code=ErrorCode.PDF_EXTRACTION_FAILED,
        status_code=500,
        title="Unable to Read Resume",
        message="We couldn't extract text from your resume.",
        action="Make sure your PDF contains searchable text, not just images."
    ),
    ErrorCode.AI_SERVICE_ERROR: UserFriendlyError(
        code=ErrorCode.AI_SERVICE_ERROR,
        status_code=500,
        title="Analysis Temporarily Unavailable",
        message="Our AI service is temporarily busy.",
        action="Please try again in a few seconds."
    ),
    ErrorCode.INTERNAL_ERROR: UserFriendlyError(
        code=ErrorCode.INTERNAL_ERROR,
        status_code=500,
        title="Something Went Wrong",
        message="An unexpected error occurred.",
        action="Please try again. Our team has been notified."
    ),
}


def get_user_error(code: ErrorCode) -> dict:
    """Get user-friendly error response for an error code"""
    error = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR])
    
    response = {
        "error": error.title,
        "message": error.message,
        "code": error.code.value,
    }
    
    if error.action:
        response["action"] = error.action
    
    if error.upgrade_url:
        response["upgrade_url"] = error.upgrade_url
    
    if error.retry_after:
        response["retry_after"] = error.retry_after
    
    return response


def get_error_status_code(code: ErrorCode) -> int:
    """Get HTTP status code for an error"""
    error = ERROR_MESSAGES.get(code, ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR])
    return error.status_code
