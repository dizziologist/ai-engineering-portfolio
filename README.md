# AI Engineering Portfolio

A collection of practical AI engineering projects built with Python and the Gemini API — focused on real-world tasks like structured data extraction and AI-assisted decision support.

## Projects

### 1. Structured Data Extractor
Takes messy, unstructured text (emails, invoices, notes) and extracts clean, structured JSON data using the Gemini API's structured output feature.

📂 [`structured-data-extractor/`](./structured-data-extractor)

### 2. Resume / Job Match Scorer + Web App
Compares a CV against a job description and returns a match score, strengths, gaps, and suggestions — combining a custom Python skills-matching engine with Gemini's contextual analysis. Includes a Streamlit web interface with PDF upload and job URL scraping.

📂 [`resume-job-matcher/`](./resume-job-matcher)

**Run the web app:**
```bash
cd resume-job-matcher
pip install -r requirements.txt
streamlit run app.py
```

## Tech Stack
- Python
- Google Gemini API (structured outputs)
- Streamlit (web interface)
- PyPDF2 (PDF parsing)
- BeautifulSoup (web scraping)

## About
Built by Promise Lamola as part of a hands-on journey from no-code/low-code AI automation into writing AI-integrated Python applications.
