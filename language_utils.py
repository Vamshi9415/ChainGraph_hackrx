
import re
import logging
from typing import Dict

from config import LANG_DETECT_AVAILABLE

# Import langdetect conditionally since we check LANG_DETECT_AVAILABLE
try:
    import langdetect
except ImportError:
    pass

# --- Enhanced Language Detection ---
def detect_language_robust(text: str) -> str:
    """Enhanced language detection with better accuracy"""
    if not LANG_DETECT_AVAILABLE or not text.strip():
        return "en"

    try:
        cleaned_text = re.sub(r'https?://\S+', '', text)
        cleaned_text = re.sub(r'\d+', '', cleaned_text)
        cleaned_text = re.sub(r'[^\w\s]', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        sample_text = cleaned_text[:5000] if len(cleaned_text) > 5000 else cleaned_text

        if len(sample_text.split()) < 10:
            return "en"

        detected_langs = []
        for _ in range(3):
            try:
                detected_langs.append(langdetect.detect(sample_text))
            except:
                pass

        if not detected_langs:
            return "en"

        from collections import Counter
        most_common = Counter(detected_langs).most_common(1)[0][0]

        supported_langs = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar', 'hi', 'bn', 'te', 'ta', 'mr', 'gu', 'ml']
        return most_common if most_common in supported_langs else "en"

    except Exception as e:
        logging.warning(f"Language detection failed: {e}")
        return "en"

def get_language_name(lang_code: str) -> str:
    """Get full language name from language code"""
    lang_mapping = {
        'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
        'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean',
        'ar': 'Arabic', 'hi': 'Hindi', 'bn': 'Bengali', 'te': 'Telugu', 'ta': 'Tamil',
        'mr': 'Marathi', 'gu': 'Gujarati', 'ml': 'Malayalam'
    }
    return lang_mapping.get(lang_code, 'English')