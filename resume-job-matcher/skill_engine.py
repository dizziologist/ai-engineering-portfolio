import re
"""
Skill Engine
-------------
Extracts skills from CV and job description text,
then compares them using Python sets.
"""

# A comprehensive list of tech/AI skills to look for
KNOWN_SKILLS = {
    # Programming
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
    # Data
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Pandas", "NumPy",
    # AI/ML
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "Keras",
    "OpenAI", "Gemini", "Claude", "LLM", "LangChain", "Hugging Face", "NLP",
    "Artificial Intelligence", "AI Engineer", "AI Developer", "AI Consultant",
    # Cloud
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform",
    # Web
    "Flask", "Django", "FastAPI", "React", "Node.js", "HTML", "CSS", "REST API", "GraphQL",
    # Automation
    "Make.com", "Zapier", "Botpress", "VAPI", "Twilio", "Airtable", "n8n",
    "No-Code", "Low-Code", "AI Automation", "AI Workflow", "AI Application",
    # Data Viz
    "Power BI", "Tableau", "Excel", "Looker", "Matplotlib", "Seaborn",
    # Tools
    "Git", "GitHub", "GitLab", "CI/CD", "Jenkins", "Jira", "Confluence",
    "Salesforce", "HubSpot", "Figma", "VS Code",
    # Other
    "Linux", "Bash", "Shell Scripting", "Prompt Engineering", "RAG",
    "Whisper", "Speech-to-Text", "Computer Vision",
    # Client-facing / role skills (matches THIS specific job posting)
    "Client-Facing", "Client Engagement", "Solution Implementation",
    "AI Training", "AI Literacy", "Robotics Training",
}
def extract_skills(text: str) -> set:
    """
    Scan text and return which known skills are mentioned.
    
    Example:
        text = "I know Python, SQL, and Power BI"
        returns: {"Python", "SQL", "Power BI"}
    """
    if not text:
        return set()
    
    # Make text easier to search (lowercase for matching)
    text_lower = text.lower()
    
    found_skills = set()
    
    for skill in KNOWN_SKILLS:
        # Check if skill name appears in the text
        # We use word boundaries so "Java" doesn't match "JavaScript"
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    
    return found_skills
def compare_skills(cv_text: str, job_text: str) -> dict:
    """
    Extract skills from both CV and job description,
    then calculate matches, gaps, and extras.
    Returns a dictionary with:
    - cv_skills: what skills the CV has
    - job_skills: what skills the job wants
    - matching: skills in both (good!)
    - missing: skills job wants but CV doesn't have (bad!)
    - extra: skills CV has but job doesn't mention (neutral)
    - coverage: percentage of job skills covered
    """
    cv_skills = extract_skills(cv_text)
    job_skills = extract_skills(job_text)
    
    matching = cv_skills & job_skills      # Intersection: in BOTH
    missing = job_skills - cv_skills       # Difference: job wants, CV lacks
    extra = cv_skills - job_skills         # Difference: CV has, job doesn't care
    
    # Calculate coverage percentage
    coverage = 0
    if job_skills:
        coverage = round(len(matching) / len(job_skills) * 100)
    
    return {
        "cv_skills": sorted(list(cv_skills)),
        "job_skills": sorted(list(job_skills)),
        "matching": sorted(list(matching)),
        "missing": sorted(list(missing)),
        "extra": sorted(list(extra)),
        "coverage": coverage,
    }