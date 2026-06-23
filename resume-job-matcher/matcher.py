"""
Resume / Job Description Match Scorer
---------------------------------------
Paste a CV and a job description, get back:
- A match score (0-100)
- Strengths that align
- Gaps or missing skills
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key from .env (one folder up)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Define exactly what we want back from the AI
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "match_score": {
            "type": "number",
            "description": "Overall match score from 0 to 100"
        },
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of strengths that match the job requirements"
        },
        "gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of missing skills, experience, or qualifications"
        },
        "suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Actionable suggestions to improve the match"
        }
    },
    "required": ["match_score", "strengths", "gaps", "suggestions"]
}


def score_resume_against_job(resume_text: str, job_description: str, skill_data: dict = None) -> dict:
    """
    Analyze CV against job description.
    If skill_data is provided, include it in the analysis.
    """
    # Build the skill section if we have skill data
    skill_section = ""
    if skill_data:
        skill_section = f"""
SKILL ANALYSIS (from Python):
- Matching skills: {', '.join(skill_data.get('matching', []))}
- Missing skills: {', '.join(skill_data.get('missing', []))}
- Extra skills: {', '.join(skill_data.get('extra', []))}
- Skill coverage: {skill_data.get('coverage', 0)}%
"""

    prompt = f"""
You are an expert recruiter and career coach.

Compare the following RESUME against the JOB DESCRIPTION.
{skill_section}

Return structured feedback.

--- RESUME ---
{resume_text}

--- JOB DESCRIPTION ---
{job_description}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
        ),
    )
    return json.loads(response.text)


if __name__ == "__main__":
    print("Starting matcher...")

    # === PASTE YOUR REAL CV HERE ===
    my_resume = """
    John Doe
    Data Analyst | Johannesburg, South Africa
    Email: john.doe@email.com | Phone: 071-234-5678

    EXPERIENCE
    - Data Analyst at Shoprite (2023-Present)
      Built dashboards in Power BI, analyzed sales trends,
      automated weekly reports using Python and Excel VBA.
    - Junior Data Analyst at Capitec (2021-2023)
      Cleaned customer datasets, built SQL queries,
      supported fraud detection team with data pulls.

    SKILLS
    Python, SQL, Power BI, Excel, Pandas, basic machine learning
    """

    # === PASTE A REAL JOB DESCRIPTION HERE ===
    job_desc = """
    Senior Data Scientist
    Requirements:
    - 4+ years experience in data science or analytics
    - Strong Python, SQL, and cloud platforms (AWS/GCP)
    - Experience with machine learning models in production
    - Knowledge of LLMs and AI tools
    - Bachelor's degree in Computer Science, Statistics, or related field
    """

    try:
        result = score_resume_against_job(my_resume, job_desc)
        print("\n" + "=" * 50)
        print("RESULTS")
        print("=" * 50)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("ERROR occurred:", e)