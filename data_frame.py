import pandas as pd
from typing import Dict, Any
from langchain.tools import tool
from diskcache import Cache
import os

from data_models import ProcessedDocument
from config import CACHE_DIR

# --- DataFrame Results Cache ---
dataframe_cache = Cache(directory=os.path.join(CACHE_DIR, "dataframe_results"))
 
    
# --- DataFrame Tools ---
class DataFrameTools:
    """Enhanced tools for operating on extracted dataframes"""

    @tool
    @staticmethod
    def query_table(table_id: str, query: str) -> str:
        """
        Query a table using simple operations.
        Args:
            table_id: ID of the table to query
            query: Simple query like 'show', 'filter column == value', 'count'
        """
        cache_key = f"query_table:{table_id}:{query}"
        cached_result = dataframe_cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            if not hasattr(DataFrameTools, 'processed_doc') or DataFrameTools.processed_doc is None:
                return "No document has been processed."

            if table_id not in DataFrameTools.processed_doc.dataframes:
                available = ', '.join(DataFrameTools.processed_doc.dataframes.keys())
                return f"Table {table_id} not found. Available: {available}"

            df = DataFrameTools.processed_doc.dataframes[table_id]
            query_parts = query.strip().split(maxsplit=1)
            
            if not query_parts:
                return "Please specify an operation: show, filter, count, describe"

            operation = query_parts[0].lower()

            if operation == "show":
                result = DataFrameTools._format_dataframe(df)
            elif operation == "describe":
                result = f"Table: {table_id}\nDimensions: {df.shape[0]} rows × {df.shape[1]} columns\n"
                result += "Columns: " + ", ".join(df.columns.astype(str))
            elif operation == "count":
                result = f"Total rows: {df.shape[0]}"
            elif operation == "filter" and len(query_parts) > 1:
                filter_expr = query_parts[1]
                if "==" in filter_expr:
                    col, val = filter_expr.split("==", 1)
                    col, val = col.strip(), val.strip().strip('"\'')
                    if col in df.columns:
                        filtered_df = df[df[col].astype(str).str.contains(val, na=False)]
                        result = DataFrameTools._format_dataframe(filtered_df)
                    else:
                        result = f"Column '{col}' not found. Available: {', '.join(df.columns)}"
                else:
                    result = "Filter format: filter column_name == 'value'"
            else:
                result = "Supported operations: show, describe, count, filter column == 'value'"

            dataframe_cache.set(cache_key, result, expire=3600)
            return result

        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def _format_dataframe(df: pd.DataFrame, max_rows: int = 10) -> str:
        """Format DataFrame as readable text"""
        if df.empty:
            return "Empty table"
            
        formatted_df = df.copy()
        for col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].astype(str)

        if df.shape[0] > max_rows:
            formatted_df = formatted_df.head(max_rows)
            footer = f"\n... and {df.shape[0] - max_rows} more rows"
        else:
            footer = ""

        result = formatted_df.to_string(index=False)
        header = f"Table Results ({min(df.shape[0], max_rows)} of {df.shape[0]} rows):\n"
        return header + result + footer

    @staticmethod
    def register_document(processed_doc: ProcessedDocument):
        """Register processed document for tool access"""
        DataFrameTools.processed_doc = processed_doc

    @tool
    @staticmethod
    def list_available_tables() -> str:
        """List all available tables in the document"""
        if not hasattr(DataFrameTools, 'processed_doc') or DataFrameTools.processed_doc is None:
            return "No document processed."

        tables = DataFrameTools.processed_doc.dataframes
        if not tables:
            return "No tables found."

        result = "Available tables:\n"
        for table_id, df in tables.items():
            result += f"- {table_id}: {df.shape[0]} rows × {df.shape[1]} columns\n"
        
        return result

