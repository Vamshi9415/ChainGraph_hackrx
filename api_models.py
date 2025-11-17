from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    """
    Request model for document query API
    
    Attributes:
        documents: URL or path to the document to analyze
        questions: List of questions to answer based on the document
    """
    documents: str
    questions: List[str]

class QueryResponse(BaseModel):
    """
    Response model for document query API
    
    Attributes:
        answers: List of answers corresponding to the questions
    """
    answers: List[str]