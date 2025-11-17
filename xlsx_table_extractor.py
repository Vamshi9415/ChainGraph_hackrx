import re
import logging
import pandas as pd
import numpy as np
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime

from data_models import ExtractedTable

class EnhancedXLSXTableExtractor:
    """Enhanced XLSX processor with improved table extraction and formatting as Markdown"""

    @staticmethod
    def extract_tables_from_xlsx(file_content: bytes) -> List[ExtractedTable]:
        """Enhanced table extraction from XLSX with better formatting and context"""
        tables = []
        dataframes = {}

        try:
            with pd.ExcelFile(BytesIO(file_content)) as excel_file:
                sheet_names = excel_file.sheet_names
                logging.info(f"Processing {len(sheet_names)} sheets from XLSX")

                # Process each sheet with enhanced logic
                for sheet_name in sheet_names:
                    try:
                        sheet_tables = EnhancedXLSXTableExtractor._process_sheet_enhanced(
                            excel_file, sheet_name
                        )
                        tables.extend(sheet_tables)

                        # Store dataframe in memory for table operation tools
                        for table in sheet_tables:
                            if table.dataframe is not None:
                                table_id = f"{sheet_name}_{table.metadata.get('table_number', len(dataframes) + 1)}"
                                dataframes[table_id] = table.dataframe

                    except Exception as e:
                        logging.warning(f"Failed to process sheet '{sheet_name}': {e}")
                        # Add error table for debugging
                        tables.append(ExtractedTable(
                            content=f"ERROR processing sheet '{sheet_name}': {str(e)}",
                            table_type='xlsx_error',
                            location=f'Sheet: {sheet_name}',
                            metadata={'error': str(e)},
                            dataframe=None
                        ))

                # Add cross-sheet analysis
                if len(tables) > 1:
                    cross_sheet_analysis = EnhancedXLSXTableExtractor._analyze_cross_sheet_relationships(tables)
                    if cross_sheet_analysis:
                        tables.append(cross_sheet_analysis)

        except Exception as e:
            logging.error(f"Failed to process XLSX file: {e}")
            tables.append(ExtractedTable(
                content=f"XLSX Processing Error: {str(e)}",
                table_type='xlsx_error',
                location='File level',
                metadata={'error': str(e)},
                dataframe=None
            ))

        return tables

    @staticmethod
    def _process_sheet_enhanced(excel_file, sheet_name: str) -> List[ExtractedTable]:
        """Enhanced processing of individual sheet with multiple strategies"""
        sheet_tables = []

        try:
            # Strategy 1: Read with automatic header detection
            df_auto = pd.read_excel(excel_file, sheet_name=sheet_name)

            # Strategy 2: Read without headers for raw data analysis
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # Choose best strategy based on data quality
            df_chosen = EnhancedXLSXTableExtractor._choose_best_dataframe(df_auto, df_raw)

            if df_chosen.empty:
                return sheet_tables

            # Clean the dataframe
            df_cleaned = EnhancedXLSXTableExtractor._clean_dataframe(df_chosen)

            if df_cleaned.empty:
                return sheet_tables

            # Detect multiple tables in the sheet
            table_regions = EnhancedXLSXTableExtractor._detect_table_regions(df_cleaned)

            if not table_regions:
                # Treat entire sheet as one table
                table_regions = [(0, 0, len(df_cleaned)-1, len(df_cleaned.columns)-1)]

            # Process each detected table region
            for idx, (start_row, start_col, end_row, end_col) in enumerate(table_regions):
                try:
                    table_df = df_cleaned.iloc[start_row:end_row+1, start_col:end_col+1]

                    if table_df.empty:
                        continue

                    # MODIFIED: Format the table as Markdown with enhanced context
                    table_content = EnhancedXLSXTableExtractor._format_table_enhanced(
                        table_df, sheet_name, idx+1, start_row, start_col
                    )

                    # Enhanced metadata extraction
                    metadata = EnhancedXLSXTableExtractor._extract_enhanced_metadata(
                        table_df, sheet_name, idx+1
                    )

                    location = f'Sheet: {sheet_name}'
                    if len(table_regions) > 1:
                        location += f', Table: {idx+1}, Region: R{start_row+1}C{start_col+1}:R{end_row+1}C{end_col+1}'

                    # Store a clean copy of the dataframe for DataFrame tools
                    table_df_copy = table_df.copy()

                    # Convert all columns to string for better tool compatibility
                    for col in table_df_copy.columns:
                        if table_df_copy[col].dtype != 'object':
                            table_df_copy[col] = table_df_copy[col].astype(str)

                    sheet_tables.append(ExtractedTable(
                        content=table_content,
                        table_type='xlsx_markdown',
                        location=location,
                        metadata=metadata,
                        dataframe=table_df_copy
                    ))

                except Exception as e:
                    logging.warning(f"Error processing table region {idx+1} in sheet '{sheet_name}': {e}")
                    continue

        except Exception as e:
            logging.error(f"Enhanced sheet processing failed for '{sheet_name}': {e}")
            # Fallback to basic processing
            try:
                df_basic = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                if not df_basic.empty:
                    # MODIFIED: Use basic Markdown formatting as fallback
                    basic_content = EnhancedXLSXTableExtractor._format_table_basic(df_basic, sheet_name)
                    sheet_tables.append(ExtractedTable(
                        content=basic_content,
                        table_type='xlsx_markdown_fallback',
                        location=f'Sheet: {sheet_name} (Fallback)',
                        metadata={'processing_method': 'basic_fallback', 'original_error': str(e)},
                        dataframe=df_basic
                    ))
            except Exception as fallback_error:
                logging.error(f"Even basic processing failed for '{sheet_name}': {fallback_error}")

        return sheet_tables

    # --- Methods from _choose_best_dataframe to _detect_table_regions remain the same ---
    # (To keep the response concise, the unchanged helper methods are omitted. 
    #  You should keep them in your actual code.)
    @staticmethod
    def _choose_best_dataframe(df_auto: pd.DataFrame, df_raw: pd.DataFrame) -> pd.DataFrame:
        if df_auto.empty and df_raw.empty:
            return df_auto
        elif df_auto.empty:
            return df_raw
        elif df_raw.empty:
            return df_auto
        auto_score = EnhancedXLSXTableExtractor._calculate_dataframe_quality(df_auto)
        raw_score = EnhancedXLSXTableExtractor._calculate_dataframe_quality(df_raw)
        if abs(auto_score - raw_score) < 0.1:
            return df_auto
        return df_auto if auto_score > raw_score else df_raw

    @staticmethod
    def _calculate_dataframe_quality(df: pd.DataFrame) -> float:
        if df.empty:
            return 0.0
        score = 0.0
        total_cells = df.shape[0] * df.shape[1]
        if total_cells == 0:
            return 0.0
        non_null_ratio = df.count().sum() / total_cells
        score += non_null_ratio * 0.4
        numeric_cols = df.select_dtypes(include=[np.number]).shape[1]
        text_cols = df.select_dtypes(include=['object']).shape[1]
        datetime_cols = df.select_dtypes(include=['datetime']).shape[1]
        type_diversity = min(1.0, (numeric_cols + text_cols + datetime_cols) / df.shape[1])
        score += type_diversity * 0.3
        if hasattr(df.columns, 'str') and df.shape[1] > 0:
            valid_headers = sum(1 for col in df.columns if isinstance(col, str) and len(str(col).strip()) > 0)
            header_quality = valid_headers / df.shape[1]
            score += header_quality * 0.3
        return min(score, 1.0)

    @staticmethod
    def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df_cleaned = df.dropna(how='all').dropna(axis=1, how='all')
        if df_cleaned.empty:
            return df_cleaned
        df_cleaned = df_cleaned.fillna('')
        for col in df_cleaned.columns:
            if df_cleaned[col].dtype == 'object':
                df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
                df_cleaned[col] = df_cleaned[col].str.replace(r'\s+', ' ', regex=True)
        return df_cleaned

    @staticmethod
    def _detect_table_regions(df: pd.DataFrame) -> List[tuple]:
        if df.empty:
            return []
        regions = []
        if not df.empty:
            regions.append((0, 0, len(df)-1, len(df.columns)-1))
        return regions
    # --- END of unchanged methods ---

    @staticmethod
    def _format_table_enhanced(df: pd.DataFrame, sheet_name: str, table_num: int,
                               start_row: int, start_col: int) -> str:
        """
        MODIFIED: Formats the table as Markdown and adds rich context.
        """
        lines = [f"=== SHEET: {sheet_name} - TABLE {table_num} ==="]

        if df.empty:
            lines.append("EMPTY TABLE")
            return "\n".join(lines)

        # Add table context
        lines.append(f"POSITION: Starting at Row {start_row+1}, Column {start_col+1}")
        lines.append(f"DIMENSIONS: {df.shape[0]} rows × {df.shape[1]} columns")
        lines.append("")

        # *** CORE CHANGE: Convert DataFrame to Markdown table ***
        # Using index=False to avoid writing row numbers, as they are not part of the data.
        # tablefmt="grid" provides a clean, readable format.
        markdown_table = df.to_markdown(index=False, tablefmt="grid")
        lines.append("TABLE CONTENT (MARKDOWN FORMAT):")
        lines.append(markdown_table)
        lines.append("")
        
        # Add data analysis for richer context
        lines.append("DATA ANALYSIS:")
        for col in df.columns:
            col_data = df[col]
            non_empty = col_data[col_data != ''].count()
            unique_vals = col_data[col_data != ''].nunique()
            analysis = f"- Column '{str(col)}': Contains {non_empty} values ({unique_vals} unique)."
            sample_vals = col_data[col_data != ''].head(3).tolist()
            if sample_vals:
                sample_str = ", ".join([f"'{str(v)[:20]}'" for v in sample_vals])
                analysis += f" (e.g., {sample_str})"
            lines.append(analysis)

        # Check for mission-relevant content
        mission_indicators = EnhancedXLSXTableExtractor._detect_mission_content_enhanced(df)
        if mission_indicators:
            lines.append("\nMISSION CONTENT DETECTED:")
            lines.extend([f"- {indicator}" for indicator in mission_indicators])

        return "\n".join(lines)

    @staticmethod
    def _format_table_basic(df: pd.DataFrame, sheet_name: str) -> str:
        """
        MODIFIED: Basic fallback table formatting using Markdown.
        """
        lines = [f"=== SHEET: {sheet_name} (Basic Fallback Processing) ==="]

        if df.empty:
            lines.append("EMPTY SHEET")
            return "\n".join(lines)

        lines.append(f"DIMENSIONS: {df.shape[0]} rows × {df.shape[1]} columns")
        lines.append("")
        
        # *** CORE CHANGE: Convert DataFrame to basic Markdown table ***
        markdown_table = df.to_markdown(index=False)
        lines.append(markdown_table)
        
        return "\n".join(lines)

    # --- The remaining helper methods (_extract_enhanced_metadata, etc.) are unchanged ---
    # (You should keep them in your actual code.)
    @staticmethod
    def _extract_enhanced_metadata(df: pd.DataFrame, sheet_name: str, table_num: int) -> Dict[str, Any]:
        if df.empty:
            return {'error': 'Empty dataframe'}
        metadata = {
            'sheet_name': sheet_name,
            'table_number': table_num,
            'dimensions': df.shape,
            'extraction_method': 'enhanced_xlsx_processing_markdown',
            'processing_timestamp': pd.Timestamp.now().isoformat()
        }
        data_types = {}
        for col in df.columns:
            col_data = df[col][df[col] != '']
            if col_data.empty:
                data_types[str(col)] = 'empty'
            else:
                numeric_count = sum(1 for val in col_data if str(val).replace('.', '').replace('-', '').isdigit())
                if numeric_count / len(col_data) > 0.8:
                    data_types[str(col)] = 'numeric'
                elif any(keyword in str(col).lower() for keyword in ['date', 'time', 'created', 'modified']):
                    data_types[str(col)] = 'datetime'
                else:
                    data_types[str(col)] = 'text'
        metadata['column_types'] = data_types
        total_cells = df.shape[0] * df.shape[1]
        non_empty_cells = sum(1 for col in df.columns for val in df[col] if val != '')
        metadata['data_density'] = non_empty_cells / total_cells if total_cells > 0 else 0
        metadata['non_empty_cells'] = non_empty_cells
        metadata['contains_mission_data'] = EnhancedXLSXTableExtractor._check_for_mission_data_enhanced(df)
        all_text = ' '.join([str(val) for col in df.columns for val in df[col] if val != ''])
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']+'
        urls_found = re.findall(url_pattern, all_text)
        metadata['urls_found'] = len(urls_found)
        metadata['contains_urls'] = len(urls_found) > 0
        return metadata

    @staticmethod
    def _detect_mission_content_enhanced(df: pd.DataFrame) -> List[str]:
        indicators = []
        if df.empty:
            return indicators
        column_text = ' '.join([str(col).lower() for col in df.columns])
        mission_keywords = ['city', 'flight', 'landmark', 'token', 'api', 'url', 'mission', 'favourite']
        for keyword in mission_keywords:
            if keyword in column_text:
                indicators.append(f"Mission keyword '{keyword}' found in column headers")
        all_data = [str(val).lower() for col in df.columns for val in df[col] if pd.notna(val) and val != '']
        content_text = ' '.join(all_data)
        patterns = {
            'city': r'\b[A-Za-z]+(?:\s+[A-Za-z]+)*(?:\s+city)?\b',
            'flight': r'\b[A-Z]{1,3}\d{3,4}\b',
            'url': r'https?://[^\s<>"\']+',
            'api': r'\bapi\b|\bendpoint\b',
            'token': r'\btoken\b|\bsecret\b'
        }
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content_text)
            if matches:
                indicators.append(f"Found {len(matches)} {pattern_name} pattern(s): {matches[:3]}...")
        return indicators

    @staticmethod
    def _check_for_mission_data_enhanced(df: pd.DataFrame) -> bool:
        if df.empty:
            return False
        indicators = EnhancedXLSXTableExtractor._detect_mission_content_enhanced(df)
        return len(indicators) > 0

    @staticmethod
    def _analyze_cross_sheet_relationships(tables: List[ExtractedTable]) -> Optional[ExtractedTable]:
        try:
            analysis_parts = ["=== CROSS-SHEET ANALYSIS ==="]
            sheet_names = [table.metadata['sheet_name'] for table in tables if 'sheet_name' in table.metadata]
            if len(set(sheet_names)) > 1:
                analysis_parts.append(f"WORKBOOK CONTAINS: {len(set(sheet_names))} sheets")
                analysis_parts.append(f"SHEET NAMES: {', '.join(set(sheet_names))}")
                analysis_parts.append("")
                all_content = ' '.join([table.content for table in tables])
                if 'mission' in all_content.lower() or 'flight' in all_content.lower():
                    analysis_parts.append("CROSS-SHEET MISSION CONTENT DETECTED")
                    analysis_parts.append("This workbook may contain related mission data across multiple sheets")
                    analysis_parts.append("")
                url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']+'
                all_urls = re.findall(url_pattern, all_content)
                if all_urls:
                    analysis_parts.append(f"URLS FOUND ACROSS SHEETS: {len(all_urls)} total")
                    unique_urls = list(set(all_urls))
                    analysis_parts.extend([f"  {url}" for url in unique_urls[:5]])
                    if len(unique_urls) > 5:
                        analysis_parts.append(f"  ... and {len(unique_urls) - 5} more")
                return ExtractedTable(
                    content='\n'.join(analysis_parts),
                    table_type='xlsx_cross_analysis',
                    location='Cross-sheet analysis',
                    metadata={
                        'analysis_type': 'cross_sheet_relationships',
                        'sheets_analyzed': list(set(sheet_names)),
                        'total_urls_found': len(all_urls) if all_urls else 0
                    },
                    dataframe=None
                )
        except Exception as e:
            logging.warning(f"Cross-sheet analysis failed: {e}")
        return None

