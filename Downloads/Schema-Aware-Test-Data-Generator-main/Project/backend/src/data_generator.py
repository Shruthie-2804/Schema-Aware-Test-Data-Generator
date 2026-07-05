"""
data_generator.py
-----------------
Generates realistic fake data rows for each table in the schema,
respecting:
  - Primary key uniqueness (auto-incrementing integers)
  - Foreign key correctness (picks valid parent IDs from already-generated data)
  - NOT NULL constraints (always fills these)
  - UNIQUE constraints (tracks used values and regenerates on collision)
  - Data type matching (INTEGER, VARCHAR, DATE, DECIMAL, BOOLEAN, etc.)

Uses the Faker library for realistic values and the agent's column hints
for semantic data selection.
"""

import random
import string
from typing import Dict, List, Any, Optional, Set
from faker import Faker
from src.schema_models import SchemaModel, TableModel, ColumnModel
from src.agent import DataGeneratorAgent

# Single shared Faker instance (seed for reproducibility in tests)
fake = Faker()
Faker.seed(42)
random.seed(42)

# Status choices used for 'status' columns
STATUS_CHOICES = ["active", "inactive", "pending", "completed", "cancelled"]
GENDER_CHOICES = ["Male", "Female", "Non-binary", "Prefer not to say"]
TYPE_CHOICES = ["standard", "premium", "basic", "trial", "enterprise"]

DEPARTMENTS = [
    "Engineering", "Marketing", "Finance", "Human Resources",
    "Operations", "Sales", "Legal", "Product", "Design", "Research"
]

COURSES = [
    "Introduction to Python", "Data Structures & Algorithms",
    "Web Development", "Machine Learning", "Database Management",
    "Computer Networks", "Operating Systems", "Software Engineering",
    "Cloud Computing", "Cybersecurity"
]

PRODUCT_NAMES = [
    "Wireless Mouse", "Mechanical Keyboard", "USB-C Hub", "Monitor Stand",
    "Noise Cancelling Headphones", "Webcam HD", "Laptop Stand", "Blue LED Strip",
    "Smart Speaker", "Portable Charger", "Desk Lamp", "Cable Organiser",
    "Screen Cleaner Kit", "Mouse Pad XL", "Ethernet Adapter"
]

PRODUCT_CATEGORIES = [
    "Electronics", "Accessories", "Office Supplies",
    "Furniture", "Books", "Clothing", "Sports", "Home & Garden"
]

SEMESTERS = ["Semester 1", "Semester 2", "Semester 3",
             "Semester 4", "Semester 5", "Semester 6", "Semester 7", "Semester 8"]

GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"]


def generate_value_for_hint(hint: str, col: ColumnModel, used_values: Set) -> Any:
    """
    Generate a single fake value based on the semantic hint and column metadata.
    `used_values` tracks previously generated values for UNIQUE columns.
    """
    max_attempts = 100  # prevent infinite loops on unique collisions

    for _ in range(max_attempts):
        value = _generate_raw(hint, col)
        # Enforce UNIQUE constraint
        if col.is_unique and value in used_values:
            continue
        if col.is_unique:
            used_values.add(value)
        return value

    # Fallback: append random suffix to break uniqueness deadlock
    base = _generate_raw(hint, col)
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    value = f"{base}_{suffix}" if isinstance(base, str) else base + random.randint(1000, 9999)
    used_values.add(value)
    return value


def _generate_raw(hint: str, col: ColumnModel) -> Any:
    """Core value factory — maps hint string to a Faker/random call."""

    if hint == "primary_key":
        return None  # handled separately via counter

    if hint == "full_name":
        return fake.name()
    if hint == "first_name":
        return fake.first_name()
    if hint == "last_name":
        return fake.last_name()
    if hint == "name":
        return fake.name()

    if hint == "email":
        return fake.email()
    if hint == "phone_number":
        return fake.phone_number()[:20]  # cap at 20 chars

    if hint == "address":
        return fake.address().replace("\n", ", ")
    if hint == "city":
        return fake.city()
    if hint == "state":
        return fake.state()
    if hint == "country":
        return fake.country()
    if hint == "postcode":
        return fake.postcode()

    if hint == "product_name":
        return random.choice(PRODUCT_NAMES)
    if hint == "product_category":
        return random.choice(PRODUCT_CATEGORIES)
    if hint == "company":
        return fake.company()
    if hint == "text":
        return fake.text(max_nb_chars=200)
    if hint == "sentence":
        return fake.sentence()
    if hint == "url":
        return fake.url()
    if hint == "image_url":
        return fake.image_url()

    if hint == "decimal_amount":
        return round(random.uniform(1.0, 9999.99), 2)
    if hint == "small_decimal":
        return round(random.uniform(0.0, 100.0), 2)
    if hint == "small_int":
        return random.randint(1, 100)
    if hint == "integer":
        return random.randint(1, 10000)
    if hint == "boolean":
        return random.choice([True, False])
    if hint == "rating":
        return random.randint(1, 5)

    if hint == "status":
        return random.choice(STATUS_CHOICES)
    if hint == "gender":
        return random.choice(GENDER_CHOICES)
    if hint == "type_word":
        return random.choice(TYPE_CHOICES)

    if hint == "datetime_recent":
        return fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
    if hint == "date_of_birth":
        return fake.date_of_birth(minimum_age=18, maximum_age=70).strftime("%Y-%m-%d")
    if hint == "date_recent":
        return fake.date_this_year().strftime("%Y-%m-%d")
    if hint == "date_future":
        return fake.future_date().strftime("%Y-%m-%d")

    if hint == "course_name":
        return random.choice(COURSES)
    if hint == "department":
        return random.choice(DEPARTMENTS)
    if hint == "grade":
        return random.choice(GRADES)
    if hint == "semester":
        return random.choice(SEMESTERS)

    if hint == "user_name":
        return fake.user_name()
    if hint == "password":
        return fake.sha256()
    if hint == "uuid":
        return fake.uuid4()

    # Fallback: random word or short string
    if col.data_type in ("INTEGER",):
        return random.randint(1, 1000)
    if col.data_type in ("FLOAT", "DECIMAL"):
        return round(random.uniform(0.0, 1000.0), 2)
    if col.data_type == "BOOLEAN":
        return random.choice([True, False])
    if col.data_type in ("DATE",):
        return fake.date_this_year().strftime("%Y-%m-%d")
    if col.data_type in ("DATETIME",):
        return fake.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")

    # Default: short word, truncated to max_length
    word = fake.word()
    if col.max_length:
        word = word[:col.max_length]
    return word


def generate_table_data(
    table: TableModel,
    num_rows: int,
    column_hints: Dict[str, str],
    parent_data: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """
    Generate `num_rows` data rows for a single table.

    Args:
        table:         The TableModel for this table.
        num_rows:      How many rows to generate.
        column_hints:  {column_name → hint} from the agent classification.
        parent_data:   Already-generated data keyed by table name (for FK lookups).

    Returns:
        List of dicts, each dict representing one row {col_name: value}.
    """
    rows: List[Dict[str, Any]] = []
    # Track used values per UNIQUE column
    unique_trackers: Dict[str, Set] = {
        col.name: set() for col in table.columns if col.is_unique
    }
    # Auto-increment PK counter
    pk_counter = 1

    # Build FK lookup: {column_name: list of valid parent IDs}
    fk_lookup: Dict[str, List[Any]] = {}
    for fk in table.foreign_keys:
        parent_rows = parent_data.get(fk.ref_table.lower(), [])
        if parent_rows:
            fk_lookup[fk.column] = [row[fk.ref_column] for row in parent_rows]
        else:
            fk_lookup[fk.column] = []

    for _ in range(num_rows):
        row: Dict[str, Any] = {}

        for col in table.columns:
            # ---- Primary Key ------------------------------------------------
            if col.is_primary_key:
                row[col.name] = pk_counter
                pk_counter += 1
                continue

            # ---- Foreign Key ------------------------------------------------
            if col.name in fk_lookup:
                valid_ids = fk_lookup[col.name]
                if valid_ids:
                    row[col.name] = random.choice(valid_ids)
                else:
                    # No parent rows — use 1 as fallback (noted in limitations)
                    row[col.name] = 1
                continue

            # ---- Nullable: sometimes emit NULL ------------------------------
            if col.is_nullable and col.default_value is None:
                if random.random() < 0.12:  # ~12% chance of NULL
                    row[col.name] = None
                    continue

            # ---- Normal column using hint -----------------------------------
            hint = column_hints.get(col.name, "word")
            used = unique_trackers.get(col.name, set())
            value = generate_value_for_hint(hint, col, used)

            # Truncate strings to max_length if needed
            if isinstance(value, str) and col.max_length:
                value = value[:col.max_length]

            row[col.name] = value

        rows.append(row)

    return rows


def generate_all_data(
    schema: SchemaModel,
    generation_order: List[str],
    num_rows: int,
    agent: Optional[DataGeneratorAgent] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate data for ALL tables in the correct dependency order.

    Args:
        schema:           The parsed SchemaModel.
        generation_order: Table names in topological order (parents first).
        num_rows:         Rows per table.
        agent:            Optional agent to log ACT steps.

    Returns:
        Dict mapping table_name → list of row dicts.
    """
    all_data: Dict[str, List[Dict[str, Any]]] = {}
    column_hints_all: Dict[str, Dict[str, str]] = {}

    # Use agent hints if available, else classify on the fly
    if agent:
        column_hints_all = agent.column_hints
    else:
        from src.agent import classify_column
        for tname, table in schema.tables.items():
            column_hints_all[tname] = {col.name: classify_column(col) for col in table.columns}

    for tname in generation_order:
        table = schema.get_table(tname)
        if table is None:
            continue

        if agent:
            agent.act_start(tname)

        hints = column_hints_all.get(tname, {})
        rows = generate_table_data(table, num_rows, hints, all_data)
        all_data[tname] = rows

        if agent:
            agent.act_done(tname, len(rows))

    return all_data
