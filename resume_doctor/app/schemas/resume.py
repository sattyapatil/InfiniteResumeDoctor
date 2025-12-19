"""
Resume Analysis Response Schemas

Pydantic models for Resume Doctor API responses.
Supports both Vitals Check (lightweight) and Deep Scan (comprehensive) responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SectionFeedback(BaseModel):
    """Feedback for a single resume section"""
    section_name: str
    score: int = Field(..., ge=0, le=100)
    issues: List[str]
    actionable_fixes: List[str]


class Recommendations(BaseModel):
    """Priority-ranked recommendations for resume improvement"""
    high_priority: List[str] = []
    medium_priority: List[str] = []
    low_priority: List[str] = []


class VitalsResult(BaseModel):
    """Response schema for Vitals Check (lightweight scoring)"""
    overall_score: int = Field(..., ge=0, le=100)
    summary_feedback: str
    impact_score: int = Field(..., ge=0, le=100)
    brevity_score: int = Field(..., ge=0, le=100)
    style_score: int = Field(..., ge=0, le=100)
    experience_level: str = Field(default="mid", description="entry/mid/senior")
    industry: str = Field(default="other", description="Detected industry")
    # Empty placeholders for UI compatibility
    sections: List[SectionFeedback] = []
    missing_keywords: List[str] = []
    parsed_data: Dict[str, Any] = {}


class AnalysisResult(BaseModel):
    """Full response schema for Deep Scan (comprehensive analysis)"""
    overall_score: int = Field(..., ge=0, le=100)
    summary_feedback: str
    impact_score: int = Field(..., ge=0, le=100, description="Quantifiable results score")
    brevity_score: int = Field(..., ge=0, le=100, description="Conciseness score")
    style_score: int = Field(..., ge=0, le=100, description="Active voice/grammar score")
    
    # Optional enhanced scores
    completeness_score: Optional[int] = Field(None, ge=0, le=100, description="Section completeness")
    ats_score: Optional[int] = Field(None, ge=0, le=100, description="ATS optimization score")
    
    # Experience context
    experience_level: str = Field(default="mid", description="entry/mid/senior")
    industry: str = Field(default="other", description="Detected industry")
    
    # Detailed Breakdown
    sections: List[SectionFeedback] = []
    
    # Keyword Analysis
    missing_keywords: List[str] = []
    
    # Priority Recommendations (Deep Scan only)
    recommendations: Optional[Recommendations] = None
    
    # Parsed resume data for autofill
    parsed_data: Dict[str, Any] = Field(default_factory=dict, description="Structured resume content")

