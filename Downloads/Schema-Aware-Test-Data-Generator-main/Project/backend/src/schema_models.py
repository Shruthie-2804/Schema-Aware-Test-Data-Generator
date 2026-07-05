"""
schema_models.py
----------------
Defines the data classes (models) used to represent a parsed database schema.
These are simple Python dataclasses — no ORM or external dependencies needed.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class ColumnModel:
    """Represents a single column in a database table."""
    name: str                        # Column name, e.g., 'user_id'
    data_type: str                   # SQL data type, e.g., 'INTEGER', 'VARCHAR'
    is_primary_key: bool = False     # True if this column is a primary key
    is_nullable: bool = True         # False if NOT NULL constraint is present
    is_unique: bool = False          # True if UNIQUE constraint is present
    default_value: Optional[str] = None  # DEFAULT value if specified
    max_length: Optional[int] = None     # For VARCHAR(n), stores n

    def __repr__(self):
        flags = []
        if self.is_primary_key:
            flags.append("PK")
        if not self.is_nullable:
            flags.append("NOT NULL")
        if self.is_unique:
            flags.append("UNIQUE")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"Column({self.name}: {self.data_type}{flag_str})"


@dataclass
class ForeignKeyModel:
    """Represents a FOREIGN KEY constraint between two tables."""
    column: str              # Column in this (child) table, e.g., 'user_id'
    ref_table: str           # Referenced (parent) table name, e.g., 'users'
    ref_column: str          # Referenced column in parent table, e.g., 'id'

    def __repr__(self):
        return f"FK({self.column} -> {self.ref_table}.{self.ref_column})"


@dataclass
class TableModel:
    """Represents a complete database table with all its columns and constraints."""
    name: str                                        # Table name, e.g., 'orders'
    columns: List[ColumnModel] = field(default_factory=list)
    foreign_keys: List[ForeignKeyModel] = field(default_factory=list)

    def get_primary_keys(self) -> List[str]:
        """Return list of primary key column names."""
        return [col.name for col in self.columns if col.is_primary_key]

    def get_column_names(self) -> List[str]:
        """Return all column names in insertion order."""
        return [col.name for col in self.columns]

    def get_column(self, name: str) -> Optional[ColumnModel]:
        """Look up a column by name. Returns None if not found."""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None

    def get_fk_columns(self) -> List[str]:
        """Return list of column names that are foreign keys."""
        return [fk.column for fk in self.foreign_keys]

    def __repr__(self):
        return (
            f"Table({self.name}, "
            f"columns={len(self.columns)}, "
            f"fks={len(self.foreign_keys)})"
        )


@dataclass
class SchemaModel:
    """
    Represents the entire parsed database schema.
    Contains all tables detected from the DDL input.
    """
    tables: Dict[str, TableModel] = field(default_factory=dict)

    def add_table(self, table: TableModel):
        """Add or replace a table in the schema."""
        self.tables[table.name.lower()] = table

    def get_table(self, name: str) -> Optional[TableModel]:
        """Get a table by name (case-insensitive)."""
        return self.tables.get(name.lower())

    def table_names(self) -> List[str]:
        """Return list of all table names."""
        return list(self.tables.keys())

    def __repr__(self):
        return f"Schema({len(self.tables)} tables: {list(self.tables.keys())})"
