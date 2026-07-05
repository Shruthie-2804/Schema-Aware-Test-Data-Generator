"""
ddl_parser.py
-------------
Parses raw SQL DDL text and extracts table/column/constraint information.

Supports common DDL patterns:
  - CREATE TABLE <name> (...)
  - Column definitions: name TYPE [constraints]
  - PRIMARY KEY (col) or inline PRIMARY KEY
  - FOREIGN KEY (col) REFERENCES table(col)
  - NOT NULL, UNIQUE, DEFAULT constraints
  - VARCHAR(n), DECIMAL(p,s), etc.

No external SQL parsing library required — uses regex + string processing.
"""

import re
from typing import List, Optional
from src.schema_models import SchemaModel, TableModel, ColumnModel, ForeignKeyModel


# ---------------------------------------------------------------------------
# Helper regex patterns
# ---------------------------------------------------------------------------

# Matches: CREATE TABLE [IF NOT EXISTS] table_name (...)
CREATE_TABLE_PATTERN = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.+?)\)\s*;",
    re.IGNORECASE | re.DOTALL
)

# Matches: FOREIGN KEY (col) REFERENCES ref_table(ref_col)
FK_PATTERN = re.compile(
    r"FOREIGN\s+KEY\s*\(\s*`?(\w+)`?\s*\)\s+REFERENCES\s+`?(\w+)`?\s*\(\s*`?(\w+)`?\s*\)",
    re.IGNORECASE
)

# Matches: PRIMARY KEY (col1, col2, ...)  — table-level constraint
TABLE_PK_PATTERN = re.compile(
    r"PRIMARY\s+KEY\s*\(\s*([^)]+)\s*\)",
    re.IGNORECASE
)

# Matches: UNIQUE (col) or UNIQUE KEY name (col) — table-level
TABLE_UNIQUE_PATTERN = re.compile(
    r"UNIQUE\s+(?:KEY\s+\w+\s*)?\(\s*`?(\w+)`?\s*\)",
    re.IGNORECASE
)

# Matches inline REFERENCES on a column definition clause:
#   category_id INTEGER REFERENCES categories(id)
INLINE_FK_PATTERN = re.compile(
    r"REFERENCES\s+`?(\w+)`?\s*\(\s*`?(\w+)`?\s*\)",
    re.IGNORECASE
)

# Matches data type with optional precision/scale: VARCHAR(100), DECIMAL(10,2), INT
DATATYPE_PATTERN = re.compile(
    r"(\w+)\s*(?:\((\d+)(?:,\s*\d+)?\))?",
    re.IGNORECASE
)

# Matches DEFAULT 'value' or DEFAULT 123 or DEFAULT NULL
DEFAULT_PATTERN = re.compile(
    r"DEFAULT\s+('(?:[^']*)'|\S+)",
    re.IGNORECASE
)


def split_table_body(body: str) -> List[str]:
    """
    Split the body of a CREATE TABLE statement into individual clauses.
    We must handle commas INSIDE parentheses (e.g., DECIMAL(10,2)).
    """
    clauses = []
    depth = 0
    current = []

    for char in body:
        if char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            clause = ''.join(current).strip()
            if clause:
                clauses.append(clause)
            current = []
        else:
            current.append(char)

    # Last clause
    last = ''.join(current).strip()
    if last:
        clauses.append(last)

    return clauses


def parse_column(clause: str) -> Optional[ColumnModel]:
    """
    Parse a column definition clause like:
      user_id INTEGER NOT NULL
      email VARCHAR(100) UNIQUE NOT NULL
      price DECIMAL(10,2) DEFAULT 0.0

    Returns a ColumnModel or None if the clause is not a column definition
    (e.g., it's a table-level constraint).
    """
    clause = clause.strip()
    # Skip table-level constraints
    upper = clause.upper().lstrip()
    if (upper.startswith("PRIMARY KEY") or
            upper.startswith("FOREIGN KEY") or
            upper.startswith("UNIQUE") or
            upper.startswith("CONSTRAINT") or
            upper.startswith("INDEX") or
            upper.startswith("KEY")):
        return None

    # Tokenise
    tokens = clause.split()
    if len(tokens) < 2:
        return None

    col_name = tokens[0].strip('`"[]')
    dtype_raw = tokens[1]

    # Extract base type and max_length
    dt_match = DATATYPE_PATTERN.match(dtype_raw)
    base_type = dt_match.group(1).upper() if dt_match else dtype_raw.upper()
    max_length = int(dt_match.group(2)) if (dt_match and dt_match.group(2)) else None

    # Normalise type aliases
    type_map = {
        "INT": "INTEGER",
        "BIGINT": "INTEGER",
        "SMALLINT": "INTEGER",
        "TINYINT": "INTEGER",
        "BOOL": "BOOLEAN",
        "DOUBLE": "FLOAT",
        "NUMERIC": "DECIMAL",
        "CHAR": "VARCHAR",
        "NVARCHAR": "VARCHAR",
        "TIMESTAMP": "DATETIME",
        "STRING": "TEXT",
    }
    base_type = type_map.get(base_type, base_type)

    rest = clause[len(tokens[0]) + len(tokens[1]) + 2:]  # after "name TYPE"

    is_primary_key = bool(re.search(r"\bPRIMARY\s+KEY\b", clause, re.IGNORECASE))
    is_nullable = not bool(re.search(r"\bNOT\s+NULL\b", clause, re.IGNORECASE))
    is_unique = bool(re.search(r"\bUNIQUE\b", clause, re.IGNORECASE))

    # If column is PK, it is implicitly NOT NULL
    if is_primary_key:
        is_nullable = False

    default_val = None
    default_match = DEFAULT_PATTERN.search(rest)
    if default_match:
        default_val = default_match.group(1).strip("'")

    return ColumnModel(
        name=col_name,
        data_type=base_type,
        is_primary_key=is_primary_key,
        is_nullable=is_nullable,
        is_unique=is_unique,
        default_value=default_val,
        max_length=max_length,
    )


def parse_ddl(ddl_text: str) -> SchemaModel:
    """
    Main entry point.  Takes raw DDL SQL text and returns a SchemaModel.

    Steps:
      1. Find all CREATE TABLE blocks.
      2. For each block, split into clauses.
      3. Parse column definitions.
      4. Parse table-level PK, FK, UNIQUE constraints.
      5. Build and return SchemaModel.
    """
    schema = SchemaModel()

    # Remove single-line SQL comments
    ddl_text = re.sub(r"--[^\n]*", "", ddl_text)
    # Remove block comments
    ddl_text = re.sub(r"/\*.*?\*/", "", ddl_text, flags=re.DOTALL)

    matches = CREATE_TABLE_PATTERN.findall(ddl_text)

    if not matches:
        raise ValueError(
            "No CREATE TABLE statements found in the provided DDL. "
            "Please check the SQL syntax."
        )

    for table_name, table_body in matches:
        table = TableModel(name=table_name.lower())
        clauses = split_table_body(table_body)

        # ---- Pass 1: parse columns ----------------------------------------
        for clause in clauses:
            col = parse_column(clause)
            if col:
                table.columns.append(col)

        # ---- Pass 2: table-level PRIMARY KEY --------------------------------
        for clause in clauses:
            pk_match = TABLE_PK_PATTERN.search(clause)
            if pk_match and not FK_PATTERN.search(clause):
                pk_cols = [c.strip().strip('`"') for c in pk_match.group(1).split(",")]
                for col in table.columns:
                    if col.name in pk_cols:
                        col.is_primary_key = True
                        col.is_nullable = False

        # ---- Pass 3: table-level FOREIGN KEY --------------------------------
        for clause in clauses:
            fk_match = FK_PATTERN.search(clause)
            if fk_match:
                fk = ForeignKeyModel(
                    column=fk_match.group(1),
                    ref_table=fk_match.group(2).lower(),
                    ref_column=fk_match.group(3),
                )
                table.foreign_keys.append(fk)

        # ---- Pass 4: table-level UNIQUE ------------------------------------
        for clause in clauses:
            upper = clause.upper().lstrip()
            if upper.startswith("UNIQUE"):
                uniq_match = TABLE_UNIQUE_PATTERN.search(clause)
                if uniq_match:
                    col_name = uniq_match.group(1)
                    col = table.get_column(col_name)
                    if col:
                        col.is_unique = True

        # ---- Pass 5: inline REFERENCES on column definitions ----------------
        for clause in clauses:
            upper = clause.upper().lstrip()
            # Skip table-level FOREIGN KEY blocks (already handled in Pass 3)
            if upper.startswith("FOREIGN KEY"):
                continue
            inline_fk_match = INLINE_FK_PATTERN.search(clause)
            if inline_fk_match:
                # Extract column name — it is the first token in the clause
                tokens = clause.split()
                if tokens:
                    col_name = tokens[0].strip('`"[]')
                    ref_table = inline_fk_match.group(1).lower()
                    ref_col = inline_fk_match.group(2)
                    # Only add if not already registered via table-level FK
                    existing_fk_cols = {fk.column for fk in table.foreign_keys}
                    if col_name not in existing_fk_cols:
                        fk = ForeignKeyModel(
                            column=col_name,
                            ref_table=ref_table,
                            ref_column=ref_col,
                        )
                        table.foreign_keys.append(fk)

        schema.add_table(table)

    return schema


def summarise_schema(schema: SchemaModel) -> str:
    """Return a human-readable summary string of the parsed schema."""
    lines = [f"Schema Summary -- {len(schema.tables)} table(s) detected\n"]
    for tname, table in schema.tables.items():
        pks = table.get_primary_keys()
        lines.append(f"  Table: {table.name}")
        lines.append(f"    Columns ({len(table.columns)}): "
                     f"{', '.join(c.name for c in table.columns)}")
        lines.append(f"    Primary Keys: {', '.join(pks) if pks else 'none'}")
        if table.foreign_keys:
            for fk in table.foreign_keys:
                lines.append(f"    FK: {fk}")
        lines.append("")
    return "\n".join(lines)
