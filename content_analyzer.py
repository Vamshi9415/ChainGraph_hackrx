import re
from typing import Dict, Any

# --- UNIVERSAL CONTENT ANALYZER ---
class UniversalContentAnalyzer:
    """Analyze content patterns without domain bias"""
    
    @staticmethod
    def analyze_content_characteristics(text: str) -> Dict[str, Any]:
        """Analyze universal content characteristics"""
        
        characteristics = {
            "has_procedures": bool(re.search(r'\b(step|procedure|process|method|how to|instructions)\b', text, re.IGNORECASE)),
            "has_definitions": bool(re.search(r'\b(define|definition|means|refers to|is defined as)\b', text, re.IGNORECASE)),
            "has_lists": bool(re.search(r'(\d+\.|•|\*|\([a-z]\)|\([A-Z]\))', text)),
            "has_contact_info": bool(re.search(r'(@|phone|email|contact|tel:|fax:|\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4})', text, re.IGNORECASE)),
            "has_numerical_data": bool(re.search(r'\b\d+(\.\d+)?(%|kg|km|years?|days?|hours?|minutes?|seconds?)\b', text)),
            "has_references": bool(re.search(r'\b(see|refer to|section|clause|article|chapter|page)\s+\d+', text, re.IGNORECASE)),
            "has_structured_sections": bool(re.search(r'(===|---|\n\s*[A-Z][A-Z\s]+:|\n\s*\d+\.|\nSection|\nChapter)', text)),
            "is_conversational": len(re.findall(r'\?', text)) > len(text.split()) * 0.05,
            "is_technical": bool(re.search(r'\b(specification|parameter|algorithm|formula|equation|theorem)\b', text, re.IGNORECASE)),
            "density": len(text.split()) / max(1, len(text.split('\n'))),
            "complexity_score": UniversalContentAnalyzer._calculate_complexity(text)
        }
        
        return characteristics
    
    @staticmethod
    def _calculate_complexity(text: str) -> float:
        """Calculate text complexity based on universal metrics"""
        words = text.split()
        if not words:
            return 0.0
            
        avg_word_len = sum(len(word) for word in words) / len(words)
        
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 1:
            sentence_lens = [len(s.split()) for s in sentences if s.strip()]
            avg_sentence_len = sum(sentence_lens) / len(sentence_lens) if sentence_lens else 0
        else:
            avg_sentence_len = len(words)
        
        complexity = 0.0
        complexity += min(avg_word_len / 10, 0.3)
        complexity += min(avg_sentence_len / 30, 0.3)
        complexity += min(len(re.findall(r'[,;:]', text)) / len(words), 0.2)
        complexity += min(len(re.findall(r'\b[A-Z]{2,}\b', text)) / len(words), 0.2)
        
        return min(complexity, 1.0)

