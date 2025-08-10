# Enhanced Language-Strict Document-Targeted RAG System (v13.0)

This project implements a sophisticated, high-performance Retrieval-Augmented Generation (RAG) system designed to answer questions based on the content of various document types. It features strict language enforcement, specialized document processors, adaptive content chunking, and an intelligent retrieval pipeline with re-ranking.

A key feature is its ability to handle "mission documents"—specialized instructions that require executing a series of steps, including fetching data from live URLs, to find a specific piece of information.

This version introduces significantly **enhanced processors for PPTX and XLSX files**, enabling more structured, detailed, and context-aware data extraction.

## ✨ Core Features

- **Multi-Format Document Processing**: Handles a wide range of formats:
    - **📄 Documents**: PDF, DOCX, TXT, HTML
    - **📊 Spreadsheets**: **XLSX** (with advanced multi-sheet analysis and table formatting)
    - **🖼️ Presentations**: **PPTX** (extracting text, tables, notes, and preserving slide structure)
    - **📸 Images**: PNG, JPEG (with Pytesseract for OCR)
- **Strict Language Enforcement**: Detects the document's language and ensures all answers are generated strictly in that language, regardless of the question's language.
- **Adaptive Chunking & Retrieval**: Dynamically adjusts content chunking strategy based on document type and content. The retrieval system uses a hybrid approach with semantic search (FAISS), importance scoring, and a Cross-Encoder for re-ranking, ensuring high relevance.
- **Mission Execution Agent**: A specialized agent detects and executes multi-step "missions" described in documents. It uses tools to fetch and process data from URLs to solve complex queries.
- **Optimized Performance**: Leverages `asyncio` for concurrent request handling and a `ThreadPoolExecutor` for parallelizing CPU-bound tasks like document parsing. It also includes auto-detection for `CUDA` or `MPS` devices for accelerated model inference.
- **Robust & Scalable API**: Built with FastAPI, featuring token-based authentication, per-request logging, and detailed health check/capability endpoints.

---

## 🚀 Enhancements in This Version

### Enhanced XLSX Processor (`EnhancedXLSXTableExtractor`)
- **Multi-Strategy Parsing**: Tries different parsing strategies (with and without headers) and chooses the best one based on data quality metrics.
- **Cross-Sheet Analysis**: Generates a summary of relationships and common themes found across multiple sheets in a workbook.
- **Rich Formatting & Analysis**: Tables are not just extracted but formatted with detailed metadata, including dimensions, data density, column statistics, data type inference, and sample values.
- **Mission Content Detection**: Actively scans for keywords and patterns related to mission objectives within tables.

### Enhanced PPTX Processor (`EnhancedPPTXTextExtractor`)
- **Structured Content Extraction**: Preserves the logical structure of a presentation by identifying and separating titles, bullet points, paragraphs, and speaker notes.
- **Table Extraction**: Extracts and formats tables directly from presentation slides.
- **Hierarchical Content Parsing**: Correctly processes text from grouped shapes and maintains indentation levels for nested bullet points.
- **Comprehensive Metadata**: Extracts presentation title, author, and other core properties.

---

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.8+
- [Tesseract OCR Engine](https://github.com/tesseract-ocr/tesseract): Required for image processing. Ensure it's installed and the `tesseract` command is in your system's PATH.

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the root directory and add your authentication token. If not set, it defaults to the value in the script.
    ```env
    # .env
    AUTH_TOKEN="2b55e57dd2584f97b52854b0738dc5608ab353c4fbc8d0409b738b7b21218fbb"
    PORT=8000
    ```

---

## 🏃‍♀️ Running the Application

Once the setup is complete, run the FastAPI server using Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`.

---

## 🔌 API Endpoints

### 1. Process Document and Answer Questions

- **Endpoint**: `POST /api/v1/hackrx/run`
- **Description**: The main endpoint to submit a document URL and a list of questions. The system processes the document and returns answers.
- **Authentication**: Requires a `Bearer` token in the `Authorization` header.
- **Request Body**:
    ```json
    {
      "documents": "URL_TO_YOUR_DOCUMENT",
      "questions": [
        "What is the capital of France?",
        "Who is the main author of the report?"
      ]
    }
    ```
- **Example cURL Request**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/hackrx/run" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer 2b55e57dd2584f97b52854b0738dc5608ab353c4fbc8d0409b738b7b21218fbb" \
    -d '{
      "documents": "[https://example.com/document.pdf](https://example.com/document.pdf)",
      "questions": ["What is the primary conclusion?"]
    }'
    ```
- **Success Response (200 OK)**:
    ```json
    {
      "answers": [
        "The primary conclusion is that solar energy is a viable alternative."
      ]
    }
    ```

### 2. Health Check

- **Endpoint**: `GET /health`
- **Description**: Provides a status check of the service, including the running version, enabled features, and loaded models.
- **Example Response**:
    ```json
    {
        "status": "healthy",
        "version": "13.0 - Enhanced Language-Strict Document-Targeted RAG with Improved PPTX/XLSX Processing",
        "features": {
            "reranking": true,
            "ocr_multilingual": true,
            "language_detection": true
        },
        "models": {
            "embedding_fast": "sentence-transformers/all-MiniLM-L6-v2",
            "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "llm": "gemini-2.5-flash-lite",
            "ocr": "pytesseract"
        },
        "device": "cuda",
        "timestamp": "2025-08-10T10:48:53.000Z"
    }
    ```

### 3. System Capabilities

- **Endpoint**: `GET /api/v1/capabilities`
- **Description**: Returns a detailed JSON object outlining the system's processing capabilities for each document type, retrieval strategy, and special features.
- **Example Response Snippet**:
    ```json
    {
        "document_processing": {
            "pptx": {
                "handler": "EnhancedPPTXTextExtractor",
                "features": ["slide content extraction", "table extraction", "notes extraction", "URL detection", "bullet point processing"]
            },
            "xlsx": {
                "handler": "EnhancedXLSXTableExtractor",
                "features": ["advanced table extraction", "multi-sheet analysis", "cross-sheet relationships"]
            }
        },
        "retrieval": {
            "handler": "EnhancedRetriever",
            "features": ["vector similarity", "cross-encoder reranking", "importance filtering"]
        }
    }
    ```
