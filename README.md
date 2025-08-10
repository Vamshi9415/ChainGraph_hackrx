
This project provides a high-performance, AI-powered API designed to read, understand, and answer questions about complex documents. It bridges the gap between static files and dynamic interaction, allowing you to converse with your data—whether it's in a dense PDF report, a multi-sheet Excel file, or a corporate PowerPoint presentation.

At its core, it leverages a sophisticated **Retrieval-Augmented Generation (RAG)** pipeline to deliver accurate, context-aware answers, making information retrieval faster and more intuitive than ever before.

## Core Capabilities

This platform is more than just a text scraper; it's an end-to-end analysis engine with a powerful set of features.

-----

### Universal Document Compatibility 

The system is built to handle a wide variety of file formats, using specialized processors to extract rich, structured information from each one.

  * **Documents**: `PDF`, `DOCX`, `TXT`, `HTML`
  * **Spreadsheets (`XLSX`)**: Goes beyond simple text extraction. It performs multi-sheet analysis, intelligently parses tables (even without clear headers), and generates summaries of relationships and themes across the entire workbook.
  * **Presentations (`PPTX`)**: Preserves the logical structure of a presentation by extracting content from slides, including titles, bullet points, tables, images, and speaker notes.
  * **Images (`PNG`, `JPEG`)**: Uses an integrated Tesseract OCR engine to extract text directly from images, making visual content searchable.

-----

### Advanced AI & Processing

  * **Intelligent Retrieval & Re-ranking**: Employs a hybrid retrieval system using semantic search to find relevant information and a sophisticated Cross-Encoder to re-rank the results, ensuring the most accurate context is used to answer your question.
  * **Autonomous Mission Agent **: Can detect and execute complex, multi-step "missions" described within a document. This agent can use tools to fetch and process data from live URLs, follow a chain of logic, and deliver a final, synthesized answer.
  * **Strict Language Enforcement **: Automatically detects a document's native language (e.g., English, Spanish, Hindi, German) and ensures all generated answers are strictly in that same language, providing a seamless experience for global users.
  * **Optimized & Scalable Performance**: Built with `asyncio` and `FastAPI`, the system is designed for high-throughput, non-blocking I/O. It also auto-detects `CUDA` or `MPS` devices to leverage GPU acceleration for model inference, ensuring rapid processing times.

-----

## 🛠️ Setup and Installation

Follow these steps to get the platform running on your local machine.

### Prerequisites

  * Python 3.8+
  * **Tesseract OCR Engine**: This is required for processing text within images. You must install it on your system and ensure the `tesseract` command is available in your system's PATH. You can find instructions [here](https://github.com/tesseract-ocr/tesseract).

### Installation Steps

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/Vamshi9415/ChainGraph_hackrx
    cd ChainGraph_hackrx
    ```

2.  **Create a Virtual Environment** (Recommended)
    This keeps your project dependencies isolated.

    ```bash
    # Create the environment
    python -m venv venv

    # Activate it (command differs by OS)
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    This is a critical step for providing the necessary API keys and configuration. Create a file named `.env` in the root of your project directory. Copy the template below into this file and replace the placeholder text with your actual credentials.

    ```env
    # --- API Endpoint Security & Server Config ---
    # This token is used to secure your API endpoints via Bearer authentication.
    AUTH_TOKEN="your_secret_authentication_token_here"
    PORT=8000

    # --- LangChain & LangSmith Configuration (for Tracing & Debugging) ---
    LANGCHAIN_API_KEY="your_langchain_api_key_here"
    LANGSMITH_TRACING="true"
    LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
    LANGCHAIN_PROJECT="Appname"

    # --- API Keys for AI/LLM Models ---
    HUGGINGFACE_TOKEN="your_huggingface_token_here"
    GOOGLE_API_KEY="your_google_api_key_here"
    # here we used gemini api key 
    ```

-----

## 🏃‍♀️ Running the Application

Once the setup is complete, you can start the FastAPI server using Uvicorn.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API is now live and will be available at `http://localhost:8000`.

-----

## 🔌 API Endpoints

The platform exposes a simple yet powerful REST API for integration.

### 1\. Process a Document and Ask Questions

This is the main endpoint for the service. Submit a document URL and a list of questions to receive AI-generated answers.

  * **Method**: `POST`
  * **Endpoint**: `/api/v1/hackrx/run`
  * **Authentication**: `Bearer` Token (using the `AUTH_TOKEN` from your `.env` file).
  * **Request Body**:
    ```json
    {
      "documents": "URL_TO_YOUR_DOCUMENT",
      "questions": [
        "What is the key finding in the summary?",
        "Who is listed as the primary contact?"
      ]
    }
    ```
  * **Example `cURL` Request**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/hackrx/run" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer your_secret_authentication_token_here" \
    -d '{
      "documents": "https://example.com/document.pdf",
      "questions": ["What is the primary conclusion?"]
    }'
    ```
  * **Success Response (`200 OK`)**:
    ```json
    {
      "answers": [
        "The primary conclusion is that solar energy is a viable alternative."
      ]
    }
    ```

### 2\. Health Check

Provides a quick status check of the service, confirming it's online and operational.

  * **Method**: `GET`
  * **Endpoint**: `/health`

### 3\. System Capabilities

Returns a detailed JSON object outlining all system capabilities, including supported document handlers and enabled AI features.

  * **Method**: `GET`
  * **Endpoint**: `/api/v1/capabilities`
