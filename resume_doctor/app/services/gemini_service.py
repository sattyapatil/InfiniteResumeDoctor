"""
Gemini AI Service for Resume Deep Scan

Provides comprehensive AI-powered resume analysis using Gemini.
Uses unified GeminiClient for consistent configuration.
"""

import json
from typing import Optional
from app.services.gemini_client import gemini_client





# Comprehensive Deep Scan prompt with industry-standard scoring
DEEP_SCAN_PROMPT = """You are an expert ATS Resume Auditor with 10+ years of recruitment experience.
Analyze this resume thoroughly and provide detailed, actionable improvements.

## SCORING METHODOLOGY (Industry Standard)
Use weighted scoring formula:
- IMPACT (30%): Quantifiable achievements using metrics (%, $, #, timeframes)
- BREVITY (20%): Concise bullets (<2 lines), scannable content, no paragraphs
- STYLE (20%): Active voice, strong action verbs, professional grammar
- COMPLETENESS (15%): Essential sections present (Contact, Summary, Experience, Education, Skills)
- ATS (15%): Standard headers, keyword optimization, no graphics/tables

Overall Score = (Impact × 0.30) + (Brevity × 0.20) + (Style × 0.20) + (Completeness × 0.15) + (ATS × 0.15)

## ANALYSIS REQUIREMENTS

### Section-by-Section Analysis
For each section found (Summary, Experience, Education, Skills, Projects, Certifications, etc.):
- Assign a score 0-100
- List 2-4 specific issues
- Provide actionable fixes with rewritten examples

### Action Verb Audit
Flag weak starters like:
- "Responsible for..." → Use "Led", "Managed", "Owned"
- "Helped with..." → Use "Contributed to", "Supported", "Assisted in"
- "Worked on..." → Use "Developed", "Built", "Created"

### Quantification Check
Identify bullets lacking metrics and suggest how to add:
- Revenue/savings: "Reduced costs by $50K annually"
- Percentages: "Improved efficiency by 40%"
- Scale: "Managed team of 8 engineers"
- Timeframes: "Delivered 2 weeks ahead of schedule"

{job_description_section}

## OUTPUT FORMAT (VALID JSON ONLY - no markdown, no explanation)
{{
  "overall_score": 72,
  "summary_feedback": "Your resume demonstrates strong technical expertise but lacks quantifiable impact. Add metrics to 50%+ of experience bullets and strengthen action verbs.",
  "impact_score": 65,
  "brevity_score": 78,
  "style_score": 80,
  "sections": [
    {{
      "section_name": "Professional Summary",
      "score": 70,
      "issues": [
        "Summary is too generic, lacks specific achievements",
        "Missing key industry keywords"
      ],
      "actionable_fixes": [
        "Add: 'Senior developer with 5+ years building scalable systems, driving 40% performance improvements'",
        "Include target role keywords from job descriptions"
      ]
    }},
    {{
      "section_name": "Experience",
      "score": 68,
      "issues": [
        "Bullet 2 under 'Software Engineer' lacks quantifiable impact",
        "Uses passive voice: 'was responsible for handling...'",
        "3 of 5 bullets missing metrics"
      ],
      "actionable_fixes": [
        "Change: 'Led development of payment feature' → 'Led development of payment feature processing $2M monthly, reducing transaction failures by 35%'",
        "Replace 'Responsible for' with 'Owned' or 'Drove'",
        "Add team size or timeline: 'Collaborated with 5-person team to deliver 2 weeks ahead of schedule'"
      ]
    }},
    {{
      "section_name": "Skills",
      "score": 85,
      "issues": [
        "Well organized and comprehensive"
      ],
      "actionable_fixes": []
    }}
  ],
  "missing_keywords": ["Python", "AWS", "CI/CD", "Agile"],
  "parsed_data": {{
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "skills": ["JavaScript", "React", "Node.js"],
    "experience": [
      {{
        "role": "Software Engineer",
        "company": "Tech Corp",
        "dates": "2020-2023",
        "description": "Full-stack development"
      }}
    ],
    "education": [
      {{
        "degree": "B.S. Computer Science",
        "institution": "State University",
        "dates": "2016-2020"
      }}
    ]
  }},
  "experience_level": "mid",
  "industry": "technology",
  "recommendations": {{
    "high_priority": [
      "Add quantifiable metrics to experience bullets (revenue, %, time saved)",
      "Replace weak verbs with strong action verbs"
    ],
    "medium_priority": [
      "Add professional summary with key achievements",
      "Include relevant certifications or courses"
    ],
    "low_priority": [
      "Add LinkedIn profile URL",
      "Consider adding a Projects section for side work"
    ]
  }}
}}

## RULES
- experience_level: "entry" (<2 years), "mid" (2-7 years), "senior" (7+ years)
- industry: technology, finance, healthcare, marketing, education, legal, engineering, consulting, other
- Provide specific, actionable fixes with example rewrites
- If job description provided, compare keywords and list truly missing ones
- parsed_data should extract actual resume content accurately

## RESUME TEXT
{resume_text}
"""


JOB_DESCRIPTION_SECTION = """### Keyword Analysis (Job Description Provided)
Compare resume keywords against the target job description.
Identify missing critical keywords that appear in JD but not resume.
Note: Only list keywords that are genuinely missing and relevant.

## TARGET JOB DESCRIPTION
{job_description}
"""


def analyze_with_gemini(pdf_content: bytes, job_description: Optional[str] = None) -> str:
    """
    Deep Scan analysis using Gemini AI.
    
    Performs comprehensive resume analysis including:
    - Industry-standard ATS scoring (weighted formula)
    - Section-by-section feedback with specific issues
    - Actionable fixes with rewritten examples
    - Keyword gap analysis (if job description provided)
    - Priority-ranked recommendations
    
    Args:
        pdf_content: Raw PDF bytes (Gemini can read PDFs directly)
        job_description: Optional target job description for keyword matching
        
    Returns:
        JSON string with full analysis results
    """
    # Build prompt with optional job description section
    if job_description:
        jd_section = JOB_DESCRIPTION_SECTION.format(job_description=job_description[:3000])
    else:
        jd_section = "### Note: No job description provided. Analyze for general ATS optimization."
    
    prompt = DEEP_SCAN_PROMPT.format(
        job_description_section=jd_section,
        resume_text="{PDF_CONTENT}"  # Placeholder, actual PDF passed as content
    )

    try:
        # Use unified Gemini client for consistent model and config
        result = gemini_client.generate_json_with_pdf(pdf_content, prompt)
        
        # Ensure required fields exist with defaults
        return json.dumps({
            "overall_score": result.get("overall_score", 50),
            "summary_feedback": result.get("summary_feedback", "Analysis complete."),
            "impact_score": result.get("impact_score", 50),
            "brevity_score": result.get("brevity_score", 50),
            "style_score": result.get("style_score", 50),
            "sections": result.get("sections", []),
            "missing_keywords": result.get("missing_keywords", []),
            "parsed_data": result.get("parsed_data", {}),
            "experience_level": result.get("experience_level", "mid"),
            "industry": result.get("industry", "other"),
            "recommendations": result.get("recommendations", {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": []
            })
        })
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        # Return error response in expected format
        return json.dumps({
            "overall_score": 0,
            "summary_feedback": "Analysis failed to parse. Please try again.",
            "impact_score": 0,
            "brevity_score": 0,
            "style_score": 0,
            "sections": [],
            "missing_keywords": [],
            "parsed_data": {},
            "error": str(e)
        })
    except Exception as e:
        print(f"Gemini API error: {e}")
        return json.dumps({
            "overall_score": 0,
            "summary_feedback": f"Analysis service error: {str(e)}",
            "impact_score": 0,
            "brevity_score": 0,
            "style_score": 0,
            "sections": [],
            "missing_keywords": [],
            "parsed_data": {},
            "error": str(e)
        })

