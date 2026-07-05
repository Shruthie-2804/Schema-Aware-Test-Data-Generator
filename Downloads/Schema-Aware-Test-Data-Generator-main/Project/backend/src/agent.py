"""
agent.py
--------
The AI-style Agent Loop for the Schema-Aware Test Data Generator.

This module simulates an intelligent reasoning agent that:
  1. OBSERVE  — reads and understands the schema structure
  2. THINK    — analyses FK relationships and column semantics
  3. PLAN     — determines generation order and column strategies
  4. ACT      — triggers data generation
  5. VALIDATE — checks referential integrity
  6. REPORT   — summarises what was done

The "AI" column classification uses a keyword-matching heuristic to infer
what kind of data should be generated for each column based on its name and
type — simulating what an LLM would do, but using zero-cost open-source logic.
"""

import re
from typing import Dict, Any, List
from src.schema_models import SchemaModel, ColumnModel


# ---------------------------------------------------------------------------
# Column Semantic Classification
# ---------------------------------------------------------------------------

# Maps keyword patterns → Faker method hint (used by data_generator.py)
COLUMN_HINTS: Dict[str, str] = {
    # Identity
    r"\bid\b": "primary_key",
    # Names
    r"(^|_)(full_?name|customer_?name|user_?name|student_?name|employee_?name)": "full_name",
    r"(^|_)(first_?name|fname)": "first_name",
    r"(^|_)(last_?name|lname|surname)": "last_name",
    r"(^|_)name($|_)": "name",
    # Contact
    r"(^|_)(email|e_mail|mail)($|_)": "email",
    r"(^|_)(phone|mobile|cell|contact_?no|phone_?no)($|_)": "phone_number",
    # Location
    r"(^|_)(address|addr|street)($|_)": "address",
    r"(^|_)(city|town)($|_)": "city",
    r"(^|_)(state|province|region)($|_)": "state",
    r"(^|_)(country|nation)($|_)": "country",
    r"(^|_)(zip|postal|pincode|zipcode)($|_)": "postcode",
    # Product / Business
    r"(^|_)(product_?name|item_?name|product_?title)($|_)": "product_name",
    r"(^|_)(category|cat)($|_)": "product_category",
    r"(^|_)(description|desc|detail)($|_)": "text",
    r"(^|_)(brand)($|_)": "company",
    r"(^|_)(company|organisation|organization|employer)($|_)": "company",
    # Finance
    r"(^|_)(price|amount|cost|fee|charge|rate|salary|wage|total|subtotal|balance|revenue)($|_)": "decimal_amount",
    r"(^|_)(discount|tax|commission)($|_)": "small_decimal",
    r"(^|_)(quantity|qty|count|stock)($|_)": "small_int",
    # Status / Type
    r"(^|_)(status)($|_)": "status",
    r"(^|_)(gender|sex)($|_)": "gender",
    r"(^|_)(type|kind|mode|method|channel)($|_)": "type_word",
    # Dates
    r"(^|_)(created_?at|updated_?at|modified_?at|registered_?at|joined_?at)($|_)": "datetime_recent",
    r"(^|_)(date_?of_?birth|dob|birth_?date)($|_)": "date_of_birth",
    r"(^|_)(order_?date|purchase_?date|invoice_?date)($|_)": "date_recent",
    r"(^|_)(start_?date|begin_?date)($|_)": "date_recent",
    r"(^|_)(end_?date|expiry_?date|expire_?date)($|_)": "date_future",
    r"(^|_)(date)($|_)": "date_recent",
    # Education
    r"(^|_)(course_?name|course_?title|subject)($|_)": "course_name",
    r"(^|_)(department|dept)($|_)": "department",
    r"(^|_)(grade|marks|score|gpa)($|_)": "grade",
    r"(^|_)(semester|sem|term)($|_)": "semester",
    # Web
    r"(^|_)(url|website|link|webpage)($|_)": "url",
    r"(^|_)(username|user_?handle|login)($|_)": "user_name",
    r"(^|_)(password|pwd|pass_?hash)($|_)": "password",
    r"(^|_)(token|api_?key|secret)($|_)": "uuid",
    # Misc
    r"(^|_)(notes|comments|remarks|feedback|review)($|_)": "sentence",
    r"(^|_)(image|photo|avatar|picture|logo)($|_)": "image_url",
    r"(^|_)(rating|stars)($|_)": "rating",
}


def classify_column(col: ColumnModel) -> str:
    """
    Infer the best Faker data category for a column based on:
      1. Whether it is a primary key
      2. Column name patterns (semantic hints)
      3. SQL data type as a fallback

    Returns a hint string consumed by data_generator.py.
    """
    name_lower = col.name.lower()

    # Primary keys get auto-increment integers
    if col.is_primary_key:
        return "primary_key"

    # Test name against each hint pattern
    for pattern, hint in COLUMN_HINTS.items():
        if re.search(pattern, name_lower):
            return hint

    # Fallback: use data type
    dtype = col.data_type.upper()
    if dtype == "INTEGER":
        return "integer"
    elif dtype in ("FLOAT", "DECIMAL"):
        return "decimal_amount"
    elif dtype == "BOOLEAN":
        return "boolean"
    elif dtype in ("DATE",):
        return "date_recent"
    elif dtype in ("DATETIME", "TIMESTAMP"):
        return "datetime_recent"
    elif dtype in ("TEXT",):
        return "sentence"
    else:
        return "word"  # VARCHAR / unknown → random word


# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------

class DataGeneratorAgent:
    """
    A simple rule-based agent that orchestrates the full data generation
    pipeline in a visible step-by-step loop.

    Each step is logged to self.log so the UI can display the agent's
    reasoning process.
    """

    def __init__(self, schema: SchemaModel, num_rows: int = 10):
        self.schema = schema
        self.num_rows = num_rows
        self.log: List[str] = []
        self.column_hints: Dict[str, Dict[str, str]] = {}  # table → {col → hint}
        self.generation_order: List[str] = []

    def _emit(self, step: str, message: str):
        """Record an agent log entry."""
        entry = f"[{step}] {message}"
        self.log.append(entry)
        print(entry)

    # ------------------------------------------------------------------
    # Step 1 — OBSERVE
    # ------------------------------------------------------------------
    def observe(self):
        """Agent reads and describes the schema it has been given."""
        self._emit("OBSERVE", f"Schema loaded -- {len(self.schema.tables)} table(s) detected.")
        for tname, table in self.schema.tables.items():
            pks = table.get_primary_keys()
            fks = [str(fk) for fk in table.foreign_keys]
            self._emit("OBSERVE",
                       f"  Table '{tname}': {len(table.columns)} columns, "
                       f"PK={pks}, FKs={fks if fks else 'none'}")

    # ------------------------------------------------------------------
    # Step 2 — THINK
    # ------------------------------------------------------------------
    def think(self):
        """Agent classifies each column semantically."""
        self._emit("THINK", "Analysing column names and data types to infer data categories...")
        for tname, table in self.schema.tables.items():
            self.column_hints[tname] = {}
            for col in table.columns:
                hint = classify_column(col)
                self.column_hints[tname][col.name] = hint
                self._emit("THINK", f"  {tname}.{col.name} ({col.data_type}) -> {hint}")

    # ------------------------------------------------------------------
    # Step 3 — PLAN
    # ------------------------------------------------------------------
    def plan(self, generation_order: List[str]):
        """Agent records the planned generation order."""
        self.generation_order = generation_order
        self._emit("PLAN",
                   f"Generation order determined: {' -> '.join(generation_order)}")
        self._emit("PLAN",
                   f"Will generate {self.num_rows} row(s) per table.")

    # ------------------------------------------------------------------
    # Step 4 — ACT  (actual generation done in data_generator.py)
    # ------------------------------------------------------------------
    def act_start(self, table_name: str):
        self._emit("ACT", f"Generating {self.num_rows} rows for table '{table_name}'...")

    def act_done(self, table_name: str, rows_generated: int):
        self._emit("ACT", f"  [OK] {rows_generated} rows generated for '{table_name}'.")

    # ------------------------------------------------------------------
    # Step 5 — VALIDATE  (actual validation done in validators.py)
    # ------------------------------------------------------------------
    def validate_start(self):
        self._emit("VALIDATE", "Running referential integrity and constraint checks...")

    def validate_result(self, passed: bool, issues: List[str]):
        if passed:
            self._emit("VALIDATE", "  [PASS] All checks passed -- data is referentially consistent.")
        else:
            self._emit("VALIDATE", f"  [WARN] {len(issues)} issue(s) detected:")
            for issue in issues:
                self._emit("VALIDATE", f"    - {issue}")

    # ------------------------------------------------------------------
    # Step 6 — REPORT
    # ------------------------------------------------------------------
    def report(self, generated_data: Dict[str, Any]):
        self._emit("REPORT", "Generation complete. Summary:")
        for tname in self.generation_order:
            rows = generated_data.get(tname, [])
            self._emit("REPORT", f"  Table '{tname}': {len(rows)} rows generated.")
        self._emit("REPORT", "Outputs: SQL inserts, CSV files, and validation report ready.")

    def get_full_log(self) -> str:
        """Return the full agent log as a single string."""
        return "\n".join(self.log)
