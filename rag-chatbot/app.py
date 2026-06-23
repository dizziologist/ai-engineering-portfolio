"""
RAG Chatbot — Chat With Your Own Documents
--------------------------------------------
Upload PDFs, ask questions, and get answers grounded ONLY in those
documents — using embeddings for retrieval + Gemini for generation.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
import streamlit as st
from google import genai
from google.genai import types

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# Load API key from .env (one folder up)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


def extract_text_from_pdf(pdf_file) -> str:
    """Pull raw text out of an uploaded PDF."""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks (by words).
    Overlap helps avoid cutting off important context at chunk boundaries.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def embed_texts(texts: list[str]) -> np.ndarray:
    """Turn a list of text chunks into embedding vectors using Gemini."""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
    )
    vectors = [e.values for e in result.embeddings]
    return np.array(vectors)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute similarity between one vector and many vectors."""
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
    return b_norm @ a_norm


def retrieve_relevant_chunks(question: str, chunks: list[str], chunk_embeddings: np.ndarray, top_k: int = 3) -> list[str]:
    """Find the chunks most relevant to the question."""
    question_embedding = embed_texts([question])[0]
    scores = cosine_similarity(question_embedding, chunk_embeddings)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [chunks[i] for i in top_indices]


def answer_question(question: str, relevant_chunks: list[str]) -> str:
    """Send the question + relevant context to Gemini for a grounded answer.
    Retries automatically if Gemini's servers are temporarily overloaded."""
    context = "\n\n---\n\n".join(relevant_chunks)
    prompt = f"""
You are a helpful assistant. Answer the question using ONLY the context below.
If the answer isn't in the context, say you don't know based on the provided documents.

CONTEXT:
{context}

QUESTION:
{question}
"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return f"⚠️ The AI service is temporarily busy. Please try asking again in a moment. (Error: {e})"


# ============== STREAMLIT UI ==============

st.set_page_config(page_title="Chat With Your Documents", page_icon="📚")
st.title("📚 Chat With Your Documents")
st.write("Upload PDFs, then ask questions. Answers are grounded only in what you upload — this is Retrieval-Augmented Generation (RAG).")

# Keep chunks/embeddings in session so we don't re-process on every interaction
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None

uploaded_files = st.file_uploader("Upload one or more PDFs", type=["pdf"], accept_multiple_files=True)

if st.button("📥 Process Documents", type="primary"):
    if not uploaded_files:
        st.warning("Upload at least one PDF first.")
    else:
        with st.spinner("Reading and chunking documents..."):
            all_chunks = []
            for file in uploaded_files:
                text = extract_text_from_pdf(file)
                file_chunks = chunk_text(text)
                all_chunks.extend(file_chunks)

        with st.spinner(f"Generating embeddings for {len(all_chunks)} chunks..."):
            embeddings = embed_texts(all_chunks)

        st.session_state.chunks = all_chunks
        st.session_state.embeddings = embeddings
        st.success(f"✅ Processed {len(uploaded_files)} document(s) into {len(all_chunks)} searchable chunks.")

st.divider()

if st.session_state.chunks:
    question = st.text_input("Ask a question about your documents:")

    if question:
        with st.spinner("Searching documents and generating answer..."):
            relevant_chunks = retrieve_relevant_chunks(
                question, st.session_state.chunks, st.session_state.embeddings
            )
            answer = answer_question(question, relevant_chunks)

        st.subheader("💬 Answer")
        st.write(answer)

        with st.expander("📄 Source chunks used for this answer"):
            for i, chunk in enumerate(relevant_chunks, 1):
                st.markdown(f"**Chunk {i}:**")
                st.text(chunk[:500] + ("..." if len(chunk) > 500 else ""))
else:
    st.info("👆 Upload and process documents first.")

st.divider()
st.caption("Built with Streamlit + Gemini API (embeddings + generation) | Promise Lamola")