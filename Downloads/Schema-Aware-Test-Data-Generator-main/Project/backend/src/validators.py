"""
validators.py
-------------
Validates generated data for referential integrity and constraint compliance.

Checks performed:
  1. Primary key uniqueness — no duplicate PK values within a table.
  2. Foreign key consistency — every FK value in a child table exists
     as a PK value in the referenced parent table.
  3. NOT NULL compliance — no NULL in non-nullable, non-default columns.
  4. Row count verification — generated row count matches expected count.
"""

from typing import Dict, List, Any, Tuple
from src.schema_models import SchemaModel


ValidationResult = Tuple[bool, List[str]]
"""(all_passed: bool, issues: List[str])"""


def validate_primary_keys(
    table_name: str,
    rows: List[Dict[str, Any]],
    pk_columns: List[str],
) -> List[str]:
    """Check that PK values are unique within the table."""
    issues = []
    if not pk_columns:
        return issues

    seen = set()
    for i, row in enumerate(rows):
        pk_val = tuple(row.get(pk) for pk in pk_columns)
        if pk_val in seen:
            issues.append(
                f"[{table_name}] Duplicate primary key {pk_val} at row index {i}."
            )
        seen.add(pk_val)
    return issues


def validate_foreign_keys(
    schema: SchemaModel,
    all_data: Dict[str, List[Dict[str, Any]]],
) -> List[str]:
    """
    For every FK in every table, verify that each FK value in the child table
    exists as a PK value in the parent table.
    """
    issues = []

    for tname, table in schema.tables.items():
        child_rows = all_data.get(tname, [])

        for fk in table.foreign_keys:
            parent_table = schema.get_table(fk.ref_table)
            if parent_table is None:
                issues.append(
                    f"[{tname}] Referenced table '{fk.ref_table}' not found in schema."
                )
                continue

            parent_rows = all_data.get(fk.ref_table.lower(), [])
            valid_parent_ids = {row.get(fk.ref_column) for row in parent_rows}

            for i, row in enumerate(child_rows):
                fk_value = row.get(fk.column)
                if fk_value is None:
                    # NULL FK is allowed only if column is nullable
                    col = table.get_column(fk.column)
                    if col and not col.is_nullable:
                        issues.append(
                            f"[{tname}] Row {i}: FK column '{fk.column}' is NULL "
                            f"but NOT NULL is required."
                        )
                    continue

                if fk_value not in valid_parent_ids:
                    issues.append(
                        f"[{tname}] Row {i}: FK '{fk.column}' = {fk_value!r} "
                        f"does not exist in '{fk.ref_table}.{fk.ref_column}'. "
                        f"Valid values: {sorted(valid_parent_ids)}"
                    )

    return issues


def validate_not_null(
    schema: SchemaModel,
    all_data: Dict[str, List[Dict[str, Any]]],
) -> List[str]:
    """Check that no NOT NULL column contains None."""
    issues = []

    for tname, table in schema.tables.items():
        rows = all_data.get(tname, [])
        for col in table.columns:
            if not col.is_nullable and col.default_value is None:
                for i, row in enumerate(rows):
                    if row.get(col.name) is None:
                        issues.append(
                            f"[{tname}] Row {i}: Column '{col.name}' "
                            f"is NOT NULL but contains None."
                        )
    return issues


def validate_row_counts(
    all_data: Dict[str, List[Dict[str, Any]]],
    expected_count: int,
) -> List[str]:
    """Verify that every table has the expected number of rows."""
    issues = []
    for tname, rows in all_data.items():
        if len(rows) != expected_count:
            issues.append(
                f"[{tname}] Expected {expected_count} rows, "
                f"but got {len(rows)}."
            )
    return issues


def run_all_validations(
    schema: SchemaModel,
    all_data: Dict[str, List[Dict[str, Any]]],
    expected_rows: int,
) -> ValidationResult:
    """
    Run all validation checks and return a consolidated result.

    Returns:
        (passed: bool, issues: List[str])
    """
    issues: List[str] = []

    # 1. PK uniqueness per table
    for tname, table in schema.tables.items():
        rows = all_data.get(tname, [])
        pk_cols = table.get_primary_keys()
        issues.extend(validate_primary_keys(tname, rows, pk_cols))

    # 2. FK consistency
    issues.extend(validate_foreign_keys(schema, all_data))

    # 3. NOT NULL compliance
    issues.extend(validate_not_null(schema, all_data))

    # 4. Row counts
    issues.extend(validate_row_counts(all_data, expected_rows))

    passed = len(issues) == 0
    return passed, issues
