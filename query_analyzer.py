import re
from typing import Dict, Any
# --- UNIVERSAL QUERY ANALYZER ---
class UniversalQueryAnalyzer:
    """Analyze queries for universal patterns without domain bias"""
    
    @staticmethod
    def analyze_query(question: str) -> Dict[str, Any]:
        """Analyze query for universal characteristics"""
        
        question_lower = question.lower()
        
        analysis = {
            "query_type": UniversalQueryAnalyzer._classify_query_type(question_lower),
            "complexity": UniversalQueryAnalyzer._assess_complexity(question),
            "requires_procedure": bool(re.search(r'\b(how|step|process|procedure|method|way to)\b', question_lower)),
            "requires_definition": bool(re.search(r'\b(what is|define|meaning|definition|explain)\b', question_lower)),
            "requires_comparison": bool(re.search(r'\b(compare|difference|versus|vs|better|worse)\b', question_lower)),
            "requires_listing": bool(re.search(r'\b(list|enumerate|all|every|each)\b', question_lower)),
            "requires_calculation": bool(re.search(r'\b(calculate|compute|total|sum|average|percentage)\b', question_lower)),
            "requires_contact": bool(re.search(r'\b(contact|email|phone|address|reach|support)\b', question_lower)),
            "is_multi_part": len(re.findall(r'\band\b|\bor\b|\balso\b|\bsimultaneously\b|\bwhile\b', question_lower)) > 0,
            "specificity": UniversalQueryAnalyzer._assess_specificity(question),
            "expected_answer_type": UniversalQueryAnalyzer._predict_answer_type(question_lower)
        }
        
        return analysis
    
    @staticmethod
    def _classify_query_type(question_lower: str) -> str:
        """Classify query by universal type"""
        
        if question_lower.startswith('what'):
            return "definition_factual"
        elif question_lower.startswith('how'):
            return "procedural"
        elif question_lower.startswith('when'):
            return "temporal"
        elif question_lower.startswith('where'):
            return "locational"
        elif question_lower.startswith('who'):
            return "entity_identification"
        elif question_lower.startswith('why'):
            return "causal_explanation"
        elif question_lower.startswith(('is', 'are', 'can', 'will', 'does', 'do')):
            return "yes_no_verification"
        elif question_lower.startswith(('list', 'name', 'enumerate')):
            return "enumeration"
        else:
            return "general_inquiry"
    
    @staticmethod
    def _assess_complexity(question: str) -> str:
        """Assess query complexity"""
        word_count = len(question.split())
        clause_count = len(re.findall(r'[,;]', question)) + 1
        
        if word_count > 30 or clause_count > 3:
            return "high"
        elif word_count > 15 or clause_count > 2:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _assess_specificity(question: str) -> str:
        """Assess how specific the question is"""
        specific_indicators = len(re.findall(r'\b(specific|exact|particular|precise|exactly)\b', question.lower()))
        general_indicators = len(re.findall(r'\b(general|overall|any|some|typical)\b', question.lower()))
        
        if specific_indicators > general_indicators:
            return "high"
        elif general_indicators > specific_indicators:
            return "low"
        else:
            return "medium"
    
    @staticmethod
    def _predict_answer_type(question_lower: str) -> str:
        """Predict the type of answer expected"""
        
        if any(word in question_lower for word in ['yes', 'no', 'true', 'false']):
            return "boolean"
        elif any(word in question_lower for word in ['number', 'amount', 'cost', 'price', 'how many', 'how much']):
            return "numerical"
        elif any(word in question_lower for word in ['list', 'enumerate', 'all', 'every']):
            return "list"
        elif any(word in question_lower for word in ['contact', 'email', 'phone', 'address']):
            return "contact_info"
        elif any(word in question_lower for word in ['how', 'step', 'process', 'procedure']):
            return "procedure"
        else:
            return "descriptive"

