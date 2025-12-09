# Resume Doctor API Integration Guide

## Base URL
`http://localhost:8000` (or your deployed domain)

## Endpoint: Health Check & Analysis
**POST** `/api/v1/health-check`

This endpoint accepts a resume PDF and an optional job description, performs a hybrid analysis (NLP + GenAI), and returns structured feedback.

### Request
**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `file` | File (PDF) | **Yes** | The resume file to analyze. Must be a PDF. |
| `job_description` | String | No | Text of the job description to compare the resume against. |

### Response
**Content-Type:** `application/json`

```json
{
  "overall_score": 85,
  "summary_feedback": "Strong resume with good impact metrics, but could use more active verbs.",
  "impact_score": 80,
  "brevity_score": 90,
  "style_score": 75,
  "sections": [
    {
      "section_name": "Experience",
      "score": 80,
      "issues": [
        "Bullet point 1 is vague",
        "Passive voice used in recent role"
      ],
      "actionable_fixes": [
        "Use 'Spearheaded' instead of 'Led'",
        "Add metrics to point 2 (e.g., 'Increased revenue by 20%')"
      ]
    }
  ],
  "missing_keywords": [
    "Python",
    "AWS",
    "Docker"
  ],
  "parsed_data": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "skills": ["Java", "Spring", "SQL"],
    "experience": [
        {
            "role": "Software Engineer",
            "company": "Tech Corp",
            "dates": "2020 - Present"
        }
    ]
  }
}
```

### Integration Example (JavaScript/Next.js)

```javascript
const formData = new FormData();
formData.append("file", resumeFile); // File object from input
if (jobDescription) {
  formData.append("job_description", jobDescription);
}

const response = await fetch("http://localhost:8000/api/v1/health-check", {
  method: "POST",
  body: formData,
});

if (!response.ok) {
  throw new Error("Analysis failed");
}

const data = await response.json();
console.log(data.overall_score);
```

### Error Codes
- `400 Bad Request`: File is not a PDF.
- `422 Validation Error`: Missing file or invalid format.
- `500 Internal Server Error`: AI service failure or parsing error.
