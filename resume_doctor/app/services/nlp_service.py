import textstat
import re
from collections import Counter
import io
from pdfminer.high_level import extract_text
import nltk
import ssl

# Ensure NLTK data is downloaded (needed for textstat)
# Fix for macOS SSL certificate error
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.data.find('corpora/cmudict.zip')
except LookupError:
    nltk.download('cmudict')

# Strong action verbs for resume analysis
STRONG_VERBS = {
    "spearheaded", "architected", "orchestrated", "increased", "reduced", "generated",
    "developed", "managed", "led", "created", "designed", "implemented", "improved",
    "optimized", "delivered", "achieved", "launched", "initiated", "coordinated",
    "established", "executed", "resolved", "negotiated", "mentored", "supervised",
    "collaborated", "partnered", "facilitated", "streamlined", "maximized", "minimized",
    "accelerated", "boosted", "enhanced", "expanded", "generated", "pioneered",
    "transformed", "revitalized", "modernized", "automated", "integrated"
}

def analyze_text_metrics(text: str):
    """
    Analyze resume text using lightweight local methods.
    This is the "Vitals Check" - fast, free, and deterministic.
    For deep analysis (skills extraction, ATS optimization), use Gemini API.
    """
    
    # 1. Readability Score (aim for 60-80)
    readability = textstat.flesch_reading_ease(text)
    
    # 2. Action Verb Analysis using regex
    # Match word boundaries to find complete words
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Count strong verbs
    strong_verb_count = sum(1 for word in words if word in STRONG_VERBS)
    
    # Estimate total verbs using common verb patterns
    # This is a lightweight heuristic - for precise analysis, use Gemini
    verb_pattern = r'\b(ed|ing|ize|ise|ate|ify)\b'
    estimated_verbs = len(re.findall(verb_pattern, text.lower()))
    # Add strong verbs that might not match the pattern
    estimated_verbs = max(estimated_verbs, strong_verb_count)
    
    # 3. Quantifiable Impact (Numbers)
    # Looking for patterns like $10k, 20%, 5x
    numeric_pattern = r'(\$\d+(?:,\d{3})*(?:\.\d+)?(?:k|m|b)?)|(\d+(?:\.\d+)?%)|(\d+x)'
    numeric_entities = re.findall(numeric_pattern, text, re.IGNORECASE)
    
    # 4. Word count
    word_count = len(words)
    
    # 5. Contact information detection (basic regex)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    has_email = bool(re.search(email_pattern, text))
    has_phone = bool(re.search(phone_pattern, text))
    
    return {
        "readability": readability,
        "strong_verb_count": strong_verb_count,
        "strong_verb_ratio": strong_verb_count / estimated_verbs if estimated_verbs > 0 else 0,
        "quantifiable_metrics": len(numeric_entities),
        "word_count": word_count,
        "has_contact_info": has_email and has_phone
    }

def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extracts text from a PDF file using pdfminer.six.
    This library handles multi-column resume layouts better than pypdf.
    """
    try:
        # pdfminer.six handles complex layouts better
        text = extract_text(io.BytesIO(file_content))
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def vitals_check(pdf_content: bytes) -> dict:
    """
    Main entry point for the Vitals Check (Free Tier).
    Extracts text from PDF and performs lightweight local analysis.
    
    This is fast, free, and deterministic - no API calls required.
    For deep analysis, use the Deep Scan endpoint with Gemini.
    
    Args:
        pdf_content: Raw PDF file bytes
        
    Returns:
        Dictionary containing vitals metrics:
        - readability: Flesch reading ease score
        - strong_verb_count: Number of strong action verbs found
        - strong_verb_ratio: Ratio of strong verbs to total verbs
        - quantifiable_metrics: Count of numbers/percentages/multipliers
        - word_count: Total word count
        - has_contact_info: Boolean if email and phone found
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_content)
    
    if not text or len(text.strip()) < 50:
        return {
            "error": "Could not extract sufficient text from PDF",
            "readability": 0,
            "strong_verb_count": 0,
            "strong_verb_ratio": 0,
            "quantifiable_metrics": 0,
            "word_count": 0,
            "has_contact_info": False
        }
    
    # Analyze the extracted text
    metrics = analyze_text_metrics(text)
    
    return metrics

