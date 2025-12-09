from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services import gemini_service, nlp_service, scoring_engine
from app.schemas.resume import AnalysisResult
import json

router = APIRouter()

@router.post("/health-check", response_model=AnalysisResult)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(None)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # 1. Read File
    content = await file.read()
    
    # 2. Parallel Execution (Conceptual - simplified for synchronous MVP)
    # Run local NLP checks (Fast)
    text_content = nlp_service.extract_text_from_pdf(content)
    if not text_content:
        # Fallback or error if text cannot be extracted? 
        # Gemini can still read the PDF visually/structurally, so we proceed but NLP stats might be empty.
        nlp_stats = {"readability": 0, "strong_verb_ratio": 0, "quantifiable_metrics": 0}
    else:
        nlp_stats = nlp_service.analyze_text_metrics(text_content)
    
    # Run Gemini Analysis (The heavy lifter)
    try:
        ai_analysis_json = gemini_service.analyze_with_gemini(content, job_description)
        # Clean up json string if it contains markdown code blocks
        if ai_analysis_json.startswith("```json"):
            ai_analysis_json = ai_analysis_json[7:]
        if ai_analysis_json.endswith("```"):
            ai_analysis_json = ai_analysis_json[:-3]
            
        ai_data = json.loads(ai_analysis_json)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Analysis failed: {str(e)}")
    
    # 3. Merge Scores (Hybrid Scoring)
    final_data = scoring_engine.calculate_hybrid_score(ai_data, nlp_stats)
    
    return final_data
