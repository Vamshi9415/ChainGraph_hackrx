import logging
import requests
from urllib.parse import urlparse

# --- Enhanced Document Type Detection ---
def detect_document_type_strict(doc_url: str) -> str:
    """Strict document type detection based on file extensions"""
    path = urlparse(doc_url).path.lower()

    if path.endswith('.png'):
        return "png"
    elif path.endswith(('.jpg', '.jpeg')):
        return "jpeg"
    elif path.endswith('.pdf'):
        return "pdf"
    elif path.endswith(('.docx', '.doc')):
        return "docx"
    elif path.endswith(('.pptx', '.ppt')):
        return "pptx"
    elif path.endswith('.txt'):
        return "txt"
    elif path.endswith(('.xlsx', '.xls')):
        return "xlsx"
    elif path.endswith('.html') or path.endswith('.htm'):
        return "html"
    elif urlparse(doc_url).scheme in ["http", "https"]:
        return "html"

    return "unknown"

async def detect_document_type_http(doc_url: str) -> str:
    """Detect document type using HTTP HEAD request Content-Type header"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.head(doc_url, timeout=10, headers=headers, allow_redirects=True)

        if response.status_code != 200:
            response = requests.get(doc_url, timeout=10, headers=headers, stream=True)
            response.close()

        content_type = response.headers.get('Content-Type', '').lower()
        logging.info(f"Detected content type: {content_type}")

        if 'application/pdf' in content_type:
            return "pdf"
        elif 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
            return "docx"
        elif 'application/vnd.openxmlformats-officedocument.presentationml.presentation' in content_type:
            return "pptx"
        elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
            return "xlsx"
        elif 'text/html' in content_type:
            return "html"
        elif 'text/plain' in content_type:
            return "txt"
        elif 'image/png' in content_type:
            return "png"
        elif 'image/jpeg' in content_type:
            return "jpeg"
        elif 'application/json' in content_type:
            return "json"

        return detect_document_type_strict(doc_url)

    except Exception as e:
        logging.warning(f"HTTP HEAD detection failed: {e}. Falling back to extension-based detection.")
        return detect_document_type_strict(doc_url)