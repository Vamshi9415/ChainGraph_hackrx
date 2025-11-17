# --- Asynchronous Logging Functionality ---
import os
import hashlib
import aiofiles
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

class AsyncLogger:
    """Asynchronous logger for documents, questions, and answers"""
    
    def __init__(self):
        """Initialize async logger with required directories"""
        # Create necessary directories
        self.downloads_dir = "./downloads"
        self.questions_dir = "./questions"
        self.answers_dir = "./answers"
        
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.questions_dir, exist_ok=True)
        os.makedirs(self.answers_dir, exist_ok=True)
        
        self.logger = logging.getLogger("async_logger")
        
    async def log_document(self, doc_content: bytes, doc_url: str, doc_type: str, request_id: str) -> None:
        """Asynchronously log document content to downloads directory"""
        try:
            # Create a unique filename based on URL and timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            url_hash = hashlib.md5(doc_url.encode()).hexdigest()[:10]
            
            # Determine file extension
            extension = "." + doc_type if doc_type != "unknown" else ""
            filename = f"{timestamp}_{url_hash}{extension}"
            filepath = os.path.join(self.downloads_dir, filename)
            
            # Save document content asynchronously
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(doc_content)
                
            # Save metadata
            metadata = {
                "url": doc_url,
                "type": doc_type,
                "size": len(doc_content),
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "filename": filename
            }
            
            meta_filepath = os.path.join(self.downloads_dir, f"{filename}.meta.json")
            async with aiofiles.open(meta_filepath, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
                
            self.logger.info(f"Document logged successfully: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error logging document: {e}")
    
    async def log_questions(self, questions: List[str], doc_url: str, request_id: str) -> None:
        """Asynchronously log questions to questions directory"""
        try:
            # Create a unique filename based on request ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{request_id}.json"
            filepath = os.path.join(self.questions_dir, filename)
            
            # Create questions data structure
            questions_data = {
                "request_id": request_id,
                "document_url": doc_url,
                "timestamp": datetime.now().isoformat(),
                "questions": questions,
                "count": len(questions)
            }
            
            # Write questions data asynchronously
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(questions_data, indent=2))
                
            self.logger.info(f"Questions logged successfully: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error logging questions: {e}")
    
    async def log_answers(self, questions: List[str], answers: List[str], 
                         doc_url: str, request_id: str, 
                         processing_time: Optional[float] = None, 
                         metrics: Optional[Dict[str, Any]] = None) -> None:
        """Asynchronously log answers to answers directory"""
        try:
            # Create a unique filename based on request ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{request_id}.json"
            filepath = os.path.join(self.answers_dir, filename)
            
            # Combine questions and answers
            qa_pairs = []
            for i, (question, answer) in enumerate(zip(questions, answers)):
                qa_pairs.append({
                    "question_id": i + 1,
                    "question": question,
                    "answer": answer
                })
            
            # Create answers data structure
            answers_data = {
                "request_id": request_id,
                "document_url": doc_url,
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "qa_count": len(qa_pairs),
                "qa_pairs": qa_pairs
            }
            
            # Add additional metrics if provided
            if metrics:
                answers_data["metrics"] = metrics
            
            # Write answers data asynchronously
            async with aiofiles.open(filepath, 'w') as f:
                await f.write(json.dumps(answers_data, indent=2))
                
            self.logger.info(f"Answers logged successfully: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error logging answers: {e}")

# Create a global async logger instance
async_logger = AsyncLogger()

# Function to create a non-blocking task for document logging
def log_document_async(doc_content: bytes, doc_url: str, doc_type: str, request_id: str) -> None:
    """Create non-blocking task for document logging"""
    try:
        asyncio.create_task(async_logger.log_document(doc_content, doc_url, doc_type, request_id))
    except Exception as e:
        logging.error(f"Failed to create document logging task: {e}")

# Function to create a non-blocking task for questions logging
def log_questions_async(questions: List[str], doc_url: str, request_id: str) -> None:
    """Create non-blocking task for questions logging"""
    try:
        asyncio.create_task(async_logger.log_questions(questions, doc_url, request_id))
    except Exception as e:
        logging.error(f"Failed to create questions logging task: {e}")

# Function to create a non-blocking task for answers logging
def log_answers_async(questions: List[str], answers: List[str], 
                     doc_url: str, request_id: str,
                     processing_time: Optional[float] = None, 
                     metrics: Optional[Dict[str, Any]] = None) -> None:
    """Create non-blocking task for answers logging"""
    try:
        asyncio.create_task(async_logger.log_answers(
            questions, answers, doc_url, request_id, processing_time, metrics
        ))
    except Exception as e:
        logging.error(f"Failed to create answers logging task: {e}")