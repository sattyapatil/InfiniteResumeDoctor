def calculate_hybrid_score(ai_data: dict, nlp_stats: dict) -> dict:
    """
    Merges scores from Gemini (Probabilistic) and local regex analysis (Deterministic).
    """
    # Example logic: Adjust AI score based on regex verb counts and readability
    
    ai_overall = ai_data.get('overall_score', 0)
    readability = nlp_stats.get('readability', 0)
    strong_verb_ratio = nlp_stats.get('strong_verb_ratio', 0)
    
    # Normalize readability (aim for 60-80, so closer to 70 is better)
    # Simple normalization: 100 if between 60-80, else penalize
    if 60 <= readability <= 80:
        readability_score = 100
    else:
        readability_score = max(0, 100 - abs(70 - readability) * 2)
        
    # Normalize verb ratio (aim for > 30% strong verbs?)
    # Let's say 0.3 is 100 score
    verb_score = min(100, (strong_verb_ratio / 0.3) * 100)
    
    # Weighted average
    # AI Score: 70%
    # Readability: 15%
    # Verb Usage: 15%
    
    final_score = (ai_overall * 0.7) + (readability_score * 0.15) + (verb_score * 0.15)
    
    # Update the overall score in the data
    ai_data['overall_score'] = int(final_score)
    
    # Add nlp metrics to the response if needed, or just use them for scoring
    # We could add them to a 'debug' section or similar, but for now we just adjust the main score
    
    return ai_data
