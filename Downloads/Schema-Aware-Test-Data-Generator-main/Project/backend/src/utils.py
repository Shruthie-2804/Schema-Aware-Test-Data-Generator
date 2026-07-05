"""
utils.py
--------
Utility helpers shared across the project:
  - Loading DDL text from a file path
  - Formatting data previews for the Streamlit UI
  - Miscellaneous string helpers
"""

import os
from typing import Dict, List, Any
import pandas as pd


def load_ddl_from_file(file_path: str) -> str:
    """Read DDL text from a .sql file. Raises FileNotFoundError if missing."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Schema file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def rows_to_dataframe(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert a list of row dicts to a pandas DataFrame for display."""
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def truncate_string(s: str, max_len: int = 50) -> str:
    """Truncate a string for display purposes."""
    if len(s) > max_len:
        return s[:max_len] + "…"
    return s


def format_generation_order(order: List[str]) -> str:
    """Format the generation order as a readable arrow string."""
    return " -> ".join(order)


def count_fk_relationships(schema) -> int:
    """Count total foreign key relationships across all tables."""
    total = 0
    for table in schema.tables.values():
        total += len(table.foreign_keys)
    return total


def get_schema_stats(schema, all_data: Dict[str, List[Any]]) -> Dict[str, Any]:
    """Return a summary dict of schema statistics for the UI."""
    total_rows = sum(len(rows) for rows in all_data.values())
    total_cols = sum(len(t.columns) for t in schema.tables.values())
    return {
        "tables": len(schema.tables),
        "total_columns": total_cols,
        "total_rows_generated": total_rows,
        "fk_relationships": count_fk_relationships(schema),
    }
