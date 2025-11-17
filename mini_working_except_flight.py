import os
import uvicorn
import asyncio
import logging
import torch
import json
import re
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from io import BytesIO, StringIO
from typing import List, Optional, Dict, Any, Union, Set, Tuple, Callable
import aiofiles
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin, urlunparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
import zipfile
import base64
import numpy as np
import hashlib
import pickle
from functools import lru_cache
import shutil

# --- Document Specific Imports ---
import fitz  # PyMuPDF for PDFs
import docx
from email import message_from_bytes
import pandas as pd
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from PIL import Image
import pytesseract
from bs4 import BeautifulSoup
import openpyxl
from xml.etree import ElementTree as ET
import langdetect

# --- LangChain Imports ---
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnableParallel, RunnableLambda

# --- Additional Imports for Improvements ---
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.retrievers import BaseRetriever
from diskcache import Cache
from sentence_transformers import util as st_util
from sentence_transformers import CrossEncoder

from query_analyzer import UniversalQueryAnalyzer

# Import the config module
from config import (
    AUTH_TOKEN, LOG_REQUESTS_PATH, TEMP_FILES_PATH, CACHE_DIR, 
    device, RERANK_AVAILABLE, OCR_AVAILABLE, LANG_DETECT_AVAILABLE
)


from data_models import (
    ExtractedURL, ExtractedTable, ExtractedImage, 
    ProcessedDocument, ChunkMetadata
)

# In mini_working_except_flight.py
from model_init import embeddings_fast, embeddings_accurate, reranker, llm 

from api_models import QueryRequest, QueryResponse 

from auth import validate_token, bearer_scheme 

from document_type_detector import detect_document_type_strict, detect_document_type_http

from language_utils import detect_language_robust, get_language_name

from content_analyzer import UniversalContentAnalyzer

from adaptive_chunking import UniversalAdaptiveChunking 

from document_processors import TargetedDocumentProcessor, ImageOCRProcessor

from pdf_processor import EnhancedPDFProcessor

from url_extractor import URLExtractor
from xlsx_table_extractor import EnhancedXLSXTableExtractor

from data_frame import DataFrameTools

from prompt_generation import process_query_universal

# # --- DataFrame Results Cache ---
# dataframe_cache = Cache(directory=os.path.join(CACHE_DIR, "dataframe_results"))



# --- FastAPI Setup ---
app = FastAPI(title="Universal Document Analysis RAG System", version="16.1")


def setup_request_logger(request_id: str):
    """Set up a dedicated logger for each request"""
    logger = logging.getLogger(request_id)
    if not logger.handlers:
        handler = logging.FileHandler(os.path.join(LOG_REQUESTS_PATH, f"{request_id}.log"))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger




# # --- API Endpoints ---
# @app.post("/api/v1/hackrx/run", response_model=QueryResponse, dependencies=[Depends(validate_token)])
# async def run_universal_submission(request: QueryRequest):
#     """Universal RAG endpoint that works for any domain"""
#     request_id = str(uuid.uuid4())
#     logger = setup_request_logger(request_id)
    
#     try:
#         logger.info(f"Universal processing: {len(request.questions)} questions")
#         start_time = asyncio.get_event_loop().time()
        
#         answers = await process_query_universal(
#             request.documents,
#             request.questions,
#             logger,
#             request_id
#         )
        
#         end_time = asyncio.get_event_loop().time()
#         logger.info(f"Completed in {end_time - start_time:.2f} seconds")
        
#         return QueryResponse(answers=answers)
        
#     except Exception as e:
#         logger.error(f"Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         for handler in logger.handlers[:]:
#             handler.close()
#             logger.removeHandler(handler)

# 3. Modify your API endpoint to use the async logger:
@app.post("/api/v1/hackrx/run", response_model=QueryResponse, dependencies=[Depends(validate_token)])
async def run_universal_submission(request: QueryRequest):
    """Universal RAG endpoint that works for any domain"""
    request_id = str(uuid.uuid4())
    logger = setup_request_logger(request_id)
    
    try:
        logger.info(f"Universal processing: {len(request.questions)} questions")
        start_time = asyncio.get_event_loop().time()
        
        answers = await process_query_universal(
            request.documents,
            request.questions,
            logger,
            request_id
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        logger.info(f"Completed in {processing_time:.2f} seconds")
        
        return QueryResponse(answers=answers)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
            
@app.get("/health")
async def health_check():
    """Enhanced health check with feature status"""
    return {
        "status": "healthy",
        "version": "16.1 - Enhanced Universal Document Analysis RAG System",
        "approach": "domain_agnostic_with_enhanced_pptx",
        "features": {
            "universal_content_analysis": True,
            "adaptive_chunking": True,
            "universal_query_analysis": True,
            "adaptive_prompting": True,
            "multi_language_support": True,
            "mission_detection": True,
            "enhanced_pptx_processing": True,
            "comprehensive_slide_extraction": True,
            "cross_reference_resolution": True,
            "presentation_summary_generation": True,
            "reranking": RERANK_AVAILABLE,
            "ocr_support": OCR_AVAILABLE,
            "language_detection": LANG_DETECT_AVAILABLE,
        },
        "models": {
            "embedding_fast": "sentence-transformers/all-MiniLM-L6-v2" if embeddings_fast else "Not loaded",
            "embedding_accurate": "BAAI/bge-small-en-v1.5" if embeddings_accurate else "Not loaded",
            "reranker": "BAAI/bge-reranker-large" if reranker else "Not available",
            "llm": "gemini-2.5-flash-lite" if llm else "Not loaded",
            "ocr": "pytesseract" if OCR_AVAILABLE else "Not available"
        },
        "supported_formats": {
            "documents": ["pdf", "docx", "pptx", "txt", "html"],
            "images": ["png", "jpeg", "jpg"],
            "tables": ["xlsx", "embedded_tables"]
        },
        "pptx_enhancements": {
            "comprehensive_extraction": [
                "titles", "text_content", "bullet_points", "tables", 
                "images_with_ocr", "charts", "smartart", "speaker_notes"
            ],
            "advanced_features": [
                "slide_relationships", "cross_references", "hyperlinks",
                "presentation_metadata", "slide_layout_detection"
            ],
            "content_organization": [
                "structured_sections", "reference_resolution", 
                "presentation_summary", "key_slide_identification"
            ]
        },
        "content_analysis": {
            "universal_patterns": [
                "procedures", "definitions", "lists", "contact_info", 
                "numerical_data", "references", "structured_sections",
                "conversational", "technical"
            ],
            "adaptive_chunking": True,
            "complexity_assessment": True
        },
        "query_analysis": {
            "query_types": [
                "definition_factual", "procedural", "temporal", "locational",
                "entity_identification", "causal_explanation", "yes_no_verification",
                "enumeration", "general_inquiry"
            ],
            "complexity_levels": ["low", "medium", "high"],
            "multi_part_detection": True,
            "answer_type_prediction": True
        },
        "language_support": {
            "output_languages": [
                "English", "Spanish", "French", "German", "Italian", "Portuguese",
                "Hindi", "Bengali", "Telugu", "Tamil", "Marathi", "Malayalam"
            ],
            "adaptive_prompting": True,
            "cross_language_qa": True
        },
        "performance": {
            "parallel_processing": True,
            "adaptive_retrieval": True,
            "context_optimization": True,
            "smart_reranking": True,
            "enhanced_pptx_processing": True
        },
        "cache_info": {
            "dataframe_cache_enabled": True,
            "cache_dir": CACHE_DIR
        },
        "device": device,
        "timestamp": datetime.now().isoformat(),
        "user": "21mcme04",
        "system_info": {
            "universal_approach": "Content and query agnostic processing",
            "adaptive_features": "Dynamic adjustment based on content characteristics",
            "domain_independence": "No hardcoded domain-specific rules",
            "pptx_enhancement": "Comprehensive slide content extraction with relationships",
            "fixes_applied": [
                "Fixed regex escape sequence warning",
                "Ensured proper function definition order",
                "Fixed vectorstore method call"
            ]
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), workers=1)