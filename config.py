import os
import logging
import torch
from dotenv import load_dotenv

# --- Enhanced Imports ---
try:
    from sentence_transformers import CrossEncoder
    RERANK_AVAILABLE = True
except ImportError:
    RERANK_AVAILABLE = False
    logging.warning("sentence-transformers not available. Re-ranking disabled.")

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract not available. OCR features disabled.")

try:
    import langdetect
    LANG_DETECT_AVAILABLE = True
except ImportError:
    LANG_DETECT_AVAILABLE = False
    logging.warning("langdetect not available. Language detection will use fallback mechanisms.")

# --- Configuration ---
load_dotenv()
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "2b55e57dd2584f97b52854b0738dc5608ab353c4fbc8d0409b738b7b21218fbb")
LOG_REQUESTS_PATH, TEMP_FILES_PATH = "./request_logs", "./temp_files"
CACHE_DIR = "./cache"
os.makedirs(LOG_REQUESTS_PATH, exist_ok=True)
os.makedirs(TEMP_FILES_PATH, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('system.log')
    ]
)

# Device detection for optimal model loading
if torch.cuda.is_available():
    device = "cuda"
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = "mps"
else:
    device = "cpu"

logging.info(f"Using device: {device}")