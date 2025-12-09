from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SectionFeedback(BaseModel):
    section_name: str
    score: int = Field(..., ge=0, le=100)
    issues: List[str]
    actionable_fixes: List[str]

class AnalysisResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    summary_feedback: str
    impact_score: int = Field(description="0-100 score on quantifiable results")
    brevity_score: int = Field(description="0-100 score on conciseness")
    style_score: int = Field(description="0-100 score on active voice/grammar")
    
    # Detailed Breakdown
    sections: List[SectionFeedback]
    
    # Hard Skills Gap (vs Target Job)
    missing_keywords: List[str]
    
    # Metadata for UI
    parsed_data: Dict[str, Any] = Field(description="Structured JSON of the resume content for autofill")
