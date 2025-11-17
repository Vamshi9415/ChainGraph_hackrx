import logging
from io import BytesIO
import fitz  # PyMuPDF for PDFs
# --- Enhanced PDF Processor ---
class EnhancedPDFProcessor:
    """Enhanced PDF processor with better text extraction"""

    @staticmethod
    def extract_pdf_content(doc_content: bytes) -> str:
        """Extract text using sorted blocks for better layout accuracy"""
        text_parts = []
        try:
            with fitz.open(stream=BytesIO(doc_content), filetype="pdf") as pdf_doc:
                metadata = pdf_doc.metadata
                if metadata:
                    meta_parts = []
                    if metadata.get("title"):
                        meta_parts.append(f"Title: {metadata['title']}")
                    if metadata.get("author"):
                        meta_parts.append(f"Author: {metadata['author']}")
                    if metadata.get("subject"):
                        meta_parts.append(f"Subject: {metadata['subject']}")

                    if meta_parts:
                        text_parts.append("=== DOCUMENT METADATA ===")
                        text_parts.append("\n".join(meta_parts))
                        text_parts.append("")

                for page_num, page in enumerate(pdf_doc, 1):
                    blocks = page.get_text("blocks", sort=True)
                    
                    page_content = []
                    for b in blocks:
                        block_text = b[4]
                        page_content.append(block_text.strip())
                    
                    full_page_text = "\n".join(page_content)

                    if full_page_text:
                        text_parts.append(f"=== PAGE {page_num} ===")
                        text_parts.append(full_page_text)
                        text_parts.append("")

                logging.info(f"Extracted text from {len(pdf_doc)} PDF pages using sorted blocks method.")

        except Exception as e:
            logging.error(f"PDF extraction failed: {e}")
            text_parts.append(f"Error extracting PDF content: {str(e)}")

        return "\n".join(text_parts)

