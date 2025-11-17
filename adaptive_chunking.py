from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from data_models import ProcessedDocument
from content_analyzer import UniversalContentAnalyzer


# --- UNIVERSAL ADAPTIVE CHUNKING ---
class UniversalAdaptiveChunking:
    """Universal chunking that adapts to content characteristics"""
    
    @staticmethod
    def create_adaptive_chunks(processed_doc: ProcessedDocument) -> List[Document]:
        """Create chunks based on universal content characteristics"""
        
        content = processed_doc.content
        characteristics = UniversalContentAnalyzer.analyze_content_characteristics(content)
        
        chunk_params = UniversalAdaptiveChunking._determine_chunk_params(characteristics, len(content))
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_params["chunk_size"],
            chunk_overlap=chunk_params["chunk_overlap"],
            separators=chunk_params["separators"],
            keep_separator=True
        )
        
        chunks = splitter.create_documents([content])
        
        for i, chunk in enumerate(chunks):
            chunk_characteristics = UniversalContentAnalyzer.analyze_content_characteristics(chunk.page_content)
            
            chunk.metadata = {
                "chunk_id": i,
                "char_count": len(chunk.page_content),
                "word_count": len(chunk.page_content.split()),
                "importance_score": UniversalAdaptiveChunking._calculate_universal_importance(chunk.page_content, chunk_characteristics),
                "content_type": UniversalAdaptiveChunking._classify_content_type(chunk_characteristics),
                "has_key_patterns": chunk_characteristics,
                "readability": chunk_characteristics["complexity_score"]
            }
        
        return chunks
    
    @staticmethod
    def _determine_chunk_params(characteristics: Dict, content_length: int) -> Dict:
        """Determine chunking parameters based on content characteristics"""
        
        params = {
            "chunk_size": 2000,
            "chunk_overlap": 400,
            "separators": ["\n\n\n", "\n\n", "\n", ". ", "? ", "! ", "; ", ", "]
        }
        
        if characteristics["has_structured_sections"]:
            params["chunk_size"] = 2500
            params["chunk_overlap"] = 500
            params["separators"] = ["\n===", "\n---", "\nSection", "\nChapter", "\nArticle"] + params["separators"]
        
        if characteristics["has_procedures"]:
            params["chunk_size"] = 2200
            params["chunk_overlap"] = 450
            # FIXED: Properly escape the regex pattern
            params["separators"] = ["\nStep", "\n\\d+\\.", "\nProcedure"] + params["separators"]
        
        if characteristics["has_lists"]:
            params["chunk_overlap"] = 600
        
        if characteristics["complexity_score"] > 0.7:
            params["chunk_size"] = 2500
            params["chunk_overlap"] = 600
        
        if characteristics["is_conversational"]:
            params["chunk_size"] = 1800
            params["separators"] = ["\n\nQ:", "\n\nA:", "\n\n"] + params["separators"]
        
        if content_length > 100000:
            params["chunk_size"] = min(3000, int(params["chunk_size"] * 1.2))
        elif content_length < 10000:
            params["chunk_size"] = max(1000, int(params["chunk_size"] * 0.7))
        
        return params
    
    @staticmethod
    def _calculate_universal_importance(content: str, characteristics: Dict) -> float:
        """Calculate importance based on universal patterns"""
        score = 0.5
        
        if characteristics["has_structured_sections"]:
            score += 0.15
        
        if characteristics["has_procedures"]:
            score += 0.15
        
        if characteristics["has_contact_info"]:
            score += 0.2
        
        if characteristics["has_definitions"]:
            score += 0.1
        
        if characteristics["has_numerical_data"]:
            score += 0.1
        
        if characteristics["has_references"]:
            score += 0.1
        
        if characteristics["density"] > 15:
            score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def _classify_content_type(characteristics: Dict) -> str:
        """Classify content type based on universal patterns"""
        
        if characteristics["has_procedures"] and characteristics["has_lists"]:
            return "procedural_guide"
        elif characteristics["has_definitions"] and characteristics["is_technical"]:
            return "technical_reference"
        elif characteristics["has_contact_info"]:
            return "contact_information"
        elif characteristics["has_structured_sections"]:
            return "structured_document"
        elif characteristics["is_conversational"]:
            return "conversational_content"
        elif characteristics["has_numerical_data"]:
            return "data_content"
        elif characteristics["complexity_score"] > 0.7:
            return "complex_content"
        else:
            return "general_content"

