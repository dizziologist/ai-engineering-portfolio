"""
Structured Data Extractor
--------------------------
Takes messy, unstructured text (like an email, invoice, or note) and
returns clean structured JSON data using the Gemini API.
"""

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Define exactly what fields we want back, and their types.
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "sender_name": {"type": "string", "description": "Name of the person or company sending the message"},
        "amount": {"type": "number", "description": "Any monetary amount mentioned, as a plain number. Use 0 if none."},
        "currency": {"type": "string", "description": "Currency code if mentioned, e.g. USD, ZAR, EUR. Empty string if none."},
        "date": {"type": "string", "description": "Any date mentioned, in YYYY-MM-DD format if possible. Empty string if none."},
        "subject": {"type": "string", "description": "A short summary of what the text is about, max 10 words."},
        "action_required": {"type": "boolean", "description": "True if the text requires the recipient to do something."}
    },
    "required": ["sender_name", "amount", "currency", "date", "subject", "action_required"]
}


def extract_structured_data(raw_text: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Extract structured data from this text:\n\n{raw_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EXTRACTION_SCHEMA,
        ),
    )
    return json.loads(response.text)


if __name__ == "__main__":
    print("Starting script...")

    api_key = os.environ.get("GEMINI_API_KEY")
    print("API key loaded:", "Yes" if api_key else "No - THIS IS THE PROBLEM")

    sample_text = """
   Invoice SummaryR 1 152.36
Your PDF tax invoice is attached.

Customer #:	Invoice #:	Due date:	Payment method:
C0387220826	I260023338710	06 April 2026	Card / EFT
Make an online card payment. We accept any card with a CVC number.


Our banking details are listed on the attached PDF invoice.

Pay by Card

Have any Questions?
Visit our Billing FAQs or contact us at support@xneelo.com


xneelo (Pty) Ltd
Belvedere Office Park, Unit F, Bella Rosa Street,
Durbanville, 7550, South Africa


Disclaimer: xneelo.co.za/email-disclaimer
    """

    try:
        result = extract_structured_data(sample_text)
        print("Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("ERROR occurred:", e)