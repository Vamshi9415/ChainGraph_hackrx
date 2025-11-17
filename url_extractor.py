import re
from typing import List

from data_models import ExtractedURL


# --- URL Extraction ---
class URLExtractor:
    """Extract and validate URLs from document content"""

    @staticmethod
    def extract_urls(text: str) -> List[ExtractedURL]:
        """Extract URLs with context from text"""
        extracted_urls = []

        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']+'
        matches = re.finditer(url_pattern, text)

        for match in matches:
            url = match.group()
            if not url.startswith('http'):
                url = 'http://' + url

            start_idx = max(0, match.start() - 100)
            end_idx = min(len(text), match.end() + 100)
            context = text[start_idx:end_idx].strip()

            url_type = URLExtractor._categorize_url(url, context)

            extracted_urls.append(ExtractedURL(
                url=url,
                context=context,
                source_location=f"Position {match.start()}",
                confidence=0.9,
                url_type=url_type
            ))

        return extracted_urls

    @staticmethod
    def _categorize_url(url: str, context: str) -> str:
        """Categorize URL based on URL pattern and context"""
        url_lower = url.lower()
        context_lower = context.lower()

        if any(term in url_lower for term in ['myfavouritecity', 'city']):
            return 'mission_city'
        elif any(term in url_lower for term in ['flightnumber', 'flight']):
            return 'mission_flight'
        elif any(term in url_lower for term in ['api', 'endpoint']):
            return 'api_endpoint'
        elif any(term in context_lower for term in ['click', 'link', 'visit']):
            return 'navigation'
        elif any(term in url_lower for term in ['image', 'img', 'photo', 'png', 'jpg']):
            return 'image'
        else:
            return 'general'

