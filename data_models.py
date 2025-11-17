from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd

# --- Enhanced Data Classes ---
@dataclass
class ExtractedURL:
    url: str
    context: str
    source_location: str
    confidence: float
    url_type: str

@dataclass
class ExtractedTable:
    content: str
    table_type: str
    location: str
    metadata: Dict[str, Any]
    dataframe: Optional[pd.DataFrame] = None

@dataclass
class ExtractedImage:
    image_path: str
    ocr_text: str
    metadata: Dict[str, Any]
    confidence: float

@dataclass
class ProcessedDocument:
    content: str
    metadata: Dict[str, Any]
    tables: List[ExtractedTable]
    images: List[ExtractedImage]
    detected_language: str
    extracted_urls: List[ExtractedURL]
    dataframes: Dict[str, pd.DataFrame] = field(default_factory=dict)

@dataclass
class ChunkMetadata:
    chunk_id: int
    char_count: int
    word_count: int
    has_tables: bool
    has_urls: bool
    importance_score: float
    content_type: str