import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import CrossEncoder

from config import (
    device, RERANK_AVAILABLE, OCR_AVAILABLE
)

# --- Global Models ---
embeddings_fast, embeddings_accurate, reranker, llm = None, None, None, None

def initialize_models():
    global embeddings_fast, embeddings_accurate, reranker, llm

    # Fast embedding model for general use
    if embeddings_fast is None:
        try:
            embeddings_fast = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True}
            )
            logging.info("Fast embeddings model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load fast embeddings model: {e}")
            embeddings_fast = None

    # Accurate embedding model for complex documents
    if embeddings_accurate is None:
        try:
            embeddings_accurate = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-en-v1.5",
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True}
            )
            logging.info("Accurate embeddings model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load accurate embeddings model: {e}")
            embeddings_accurate = None

    # Re-ranking model
    if RERANK_AVAILABLE and reranker is None:
        try:
            reranker = CrossEncoder('BAAI/bge-reranker-large', device=device)
            logging.info("Re-ranking model loaded successfully")
        except Exception as e:
            logging.warning(f"Failed to initialize re-ranker: {e}")
            reranker = None

    # LLM model
    if llm is None:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0.0, max_tokens=512)
            logging.info("LLM loaded successfully")
        except Exception as e:
            logging.error(f"Failed to initialize LLM: {e}")
            llm = None

    if OCR_AVAILABLE:
        logging.info("Pytesseract OCR is available.")
    else:
        logging.warning("Pytesseract OCR is not available.")

# Initialize models
initialize_models()