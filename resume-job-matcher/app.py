"""
Resume / Job Match Scorer — Web App
------------------------------------
Upload a PDF CV or paste text, then provide a job description
via URL or pasted text. Get a match score with analysis.
"""

import os
import json
import io
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit as st
from skill_engine import compare_skills

# For reading PDFs
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# For reading URLs
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

# Load API key from .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Define the response format
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


def extract_text_from_pdf(pdf_file):
    """Extract text from an uploaded PDF file."""
    if PyPDF2 is None:
        st.error("PyPDF2 is not installed. Run: pip install PyPDF2")
        return None
    
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None


def extract_text_from_url(url):
    """Extract text from a webpage URL."""
    if requests is None or BeautifulSoup is None:
        st.error("Required libraries not installed. Run: pip install requests beautifulsoup4")
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up extra whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        # Limit length to avoid API token limits
        if len(cleaned_text) > 15000:
            cleaned_text = cleaned_text[:15000] + "\n\n[Content truncated due to length...]"
        
        return cleaned_text
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        st.error(f"Error parsing webpage: {e}")
        return None


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


# ============== STREAMLIT UI ==============

st.set_page_config(page_title="CV Job Match Scorer", page_icon="📄")

st.title("📄 CV Job Match Scorer")
st.write("Upload your CV and provide a job description to see how well you match.")

# ============== CV SECTION (Left) ==============
st.subheader("📝 Your CV")
cv_input_method = st.radio(
    "How do you want to provide your CV?",
    ["Upload PDF", "Paste Text"],
    horizontal=True,
    label_visibility="collapsed"
)

resume_input = ""

if cv_input_method == "Upload PDF":
    uploaded_file = st.file_uploader(
        "Upload your CV (PDF)",
        type=["pdf"],
        help="Upload your CV as a PDF file"
    )
    
    if uploaded_file is not None:
        with st.spinner("Reading PDF..."):
            resume_input = extract_text_from_pdf(uploaded_file)
        
        if resume_input:
            st.success(f"✅ PDF loaded! ({len(resume_input)} characters)")
            with st.expander("Preview extracted text"):
                preview = resume_input[:800] + "..." if len(resume_input) > 800 else resume_input
                st.text(preview)
        else:
            st.error("Could not extract text from PDF. Try pasting text manually.")
    else:
        st.info("👆 Upload a PDF file above")

else:  # Paste Text
    resume_input = st.text_area(
        "Paste your CV here...",
        height=250,
        placeholder="Paste your full CV text here..."
    )

st.divider()

# ============== JOB DESCRIPTION SECTION (Right) ==============
st.subheader("💼 Job Description")
job_input_method = st.radio(
    "How do you want to provide the job description?",
    ["Paste Text", "Enter URL"],
    horizontal=True,
    label_visibility="collapsed"
)

job_input = ""

if job_input_method == "Paste Text":
    job_input = st.text_area(
        "Paste job description here...",
        height=300,
        placeholder="Paste the full job description here..."
    )

else:  # Enter URL
    url_input = st.text_input(
        "Enter job posting URL",
        placeholder="https://www.example.com/job-posting..."
    )
    
    if url_input:
        if not url_input.startswith(('http://', 'https://')):
            st.warning("Please enter a valid URL starting with http:// or https://")
        else:
            with st.spinner("Fetching job description from URL..."):
                job_input = extract_text_from_url(url_input)
            
            if job_input:
                st.success(f"✅ URL loaded! ({len(job_input)} characters extracted)")
                with st.expander("Preview extracted text"):
                    preview = job_input[:800] + "..." if len(job_input) > 800 else job_input
                    st.text(preview)
            else:
                st.error("Could not extract text from URL. Try pasting the text manually.")

st.divider()

# ============== ANALYZE BUTTON ==============
if st.button("🔍 Analyze Match", type="primary", use_container_width=True):
    if not resume_input or not resume_input.strip():
        st.warning("⚠️ Please provide your CV (upload PDF or paste text).")
    elif not job_input or not job_input.strip():
        st.warning("⚠️ Please provide a job description (paste text or enter URL).")
    else:
        with st.spinner("Analyzing... this takes a few seconds"):
            try:
                # Step 1: Python extracts and compares skills
                skill_data = compare_skills(resume_input, job_input)
                
                # Step 2: Display skills analysis
                st.subheader("🔧 Skills Analysis (Python Engine)")
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown("**✅ Matching Skills**")
                    for skill in skill_data.get("matching", []):
                        st.markdown(f"• {skill}")
                
                with col_b:
                    st.markdown("**❌ Missing Skills**")
                    for skill in skill_data.get("missing", []):
                        st.markdown(f"• {skill}")
                
                with col_c:
                    st.markdown("**📊 Coverage**")
                    st.markdown(f"### {skill_data.get('coverage', 0)}%")
                    st.progress(skill_data.get('coverage', 0) / 100)
                
                st.divider()
                
                # Step 3: Send to Gemini with skill data for contextual analysis
                result = score_resume_against_job(resume_input, job_input, skill_data)
                
                # Display results
                score = result.get("match_score", 0)
                
                # Score with color coding
                if score >= 70:
                    color = "#2ecc71"
                    emoji = "🟢"
                    message = "Strong match!"
                elif score >= 40:
                    color = "#f39c12"
                    emoji = "🟡"
                    message = "Moderate match — room for improvement"
                else:
                    color = "#e74c3c"
                    emoji = "🔴"
                    message = "Weak match — significant gaps"
                
                st.markdown(f"## {emoji} Match Score: <span style='color:{color};font-size:52px;'><b>{score}/100</b></span>", unsafe_allow_html=True)
                st.markdown(f"*{message}*")
                
                # Results columns
                res_col1, res_col2 = st.columns(2)
                
                with res_col1:
                    st.subheader("✅ Strengths")
                    strengths = result.get("strengths", [])
                    if strengths:
                        for strength in strengths:
                            st.markdown(f"• {strength}")
                    else:
                        st.write("No specific strengths identified.")
                
                with res_col2:
                    st.subheader("⚠️ Gaps")
                    gaps = result.get("gaps", [])
                    if gaps:
                        for gap in gaps:
                            st.markdown(f"• {gap}")
                    else:
                        st.write("No major gaps identified.")
                
                # Suggestions
                st.subheader("💡 Suggestions to Improve")
                suggestions = result.get("suggestions", [])
                if suggestions:
                    for suggestion in suggestions:
                        st.markdown(f"• {suggestion}")
                else:
                    st.write("No specific suggestions.")
                    
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.info("Try again with shorter text, or check your API key.")

st.divider()
st.caption("Built with Streamlit + Gemini API | Promise Lamola")