"""
hybrid_generator.py
--------------------
Hybrid data generation engine that combines Faker (for common fields)
with AI-generated values (for domain-specific, high-level semantic fields).

Design goals:
  - Faker is the default for all standard fields (fast, free, reproducible).
  - AI is used ONLY for complex semantic fields like diagnosis, prescription,
    transaction_description, product_review, etc.
  - AI results are cached to avoid repeated API calls for the same column type.
  - Falls back gracefully to Faker if AI is unavailable.
  - Preserves all PK/FK/UNIQUE/NOT NULL constraints from the existing generator.

Column decision rules:
  AI is triggered when ALL of the following are true:
    1. Column name matches AI_COLUMN_PATTERNS (semantic/domain-specific keywords).
    2. Column data type is TEXT or VARCHAR (not INT, DATE, etc.).
    3. AI provider is available.
    4. The column is not a primary key or foreign key.

Cache key: (domain, column_name_normalized) → list of generated values
"""

import random
import re
from typing import Dict, List, Any, Optional, Set, Tuple

from src.schema_models import SchemaModel, TableModel, ColumnModel
from src.data_generator import generate_table_data, generate_value_for_hint
from src.agent import classify_column, DataGeneratorAgent
from src.ai_provider import BaseAIProvider, get_provider

# ---------------------------------------------------------------------------
# AI column patterns — columns whose values benefit from AI generation
# ---------------------------------------------------------------------------

AI_COLUMN_PATTERNS = [
    # Medical
    r"(diagnosis|diagnos)",
    r"(prescription|prescribed_medication)",
    r"(treatment_plan|treatment_protocol)",
    r"(doctor_notes|physician_notes|clinical_notes|medical_notes)",
    r"(lab_results|test_results|pathology_report)",
    r"(medical_history|patient_history)",
    r"(chief_complaint|presenting_complaint)",
    r"(surgical_notes|operative_notes)",
    # E-commerce / product
    r"(product_description|item_description)",
    r"(review_text|review_body|customer_review)",
    r"(product_review|user_review)",
    r"(return_reason|return_notes)",
    # Hospitality
    r"(special_request|guest_notes|room_notes|concierge_notes)",
    r"(hotel_feedback|stay_feedback)",
    # Banking
    r"(transaction_description|transaction_notes|transaction_narration)",
    r"(loan_purpose|loan_notes)",
    r"(insurance_claim_reason|claim_description|claim_notes)",
    # Education
    r"(assignment_description|assignment_instructions)",
    r"(course_feedback|student_feedback|lecture_notes)",
    r"(essay_topic|research_topic)",
    # Support / CRM
    r"(ticket_description|support_description|issue_details|problem_description)",
    r"(resolution_notes|agent_notes|followup_notes)",
    r"(opportunity_notes|deal_notes|lead_notes)",
    # Food / Travel
    r"(dish_description|menu_description|cuisine_notes)",
    r"(delivery_notes|order_special_instructions|special_instructions)",
    r"(itinerary_details|tour_description|travel_notes|package_description)",
    # Generic
    r"(long_description|detailed_description|full_description)",
    r"(ai_generated_field)",
]

# Compiled for performance
AI_COLUMN_COMPILED = [re.compile(p, re.IGNORECASE) for p in AI_COLUMN_PATTERNS]

# Column types that can meaningfully hold AI-generated text
AI_ELIGIBLE_TYPES = {"TEXT", "VARCHAR", "NVARCHAR", "STRING"}


# ---------------------------------------------------------------------------
# Per-column prompt templates for realistic AI generation
# ---------------------------------------------------------------------------

COLUMN_PROMPTS: Dict[str, str] = {
    "diagnosis": "List 20 short realistic medical diagnosis phrases (e.g., 'Type 2 Diabetes Mellitus', 'Acute Appendicitis'). One per line, no numbering.",
    "prescription": "List 20 realistic prescription instructions for common medications. Format: 'Drug name Xmg, Y times daily for Z days'. One per line.",
    "treatment_plan": "List 20 concise treatment plan descriptions for hospital patients. One per line.",
    "doctor_notes": "List 20 concise doctor's notes for patient visits. One per line.",
    "clinical_notes": "List 20 short clinical observation notes. One per line.",
    "product_description": "List 20 realistic e-commerce product descriptions (2 sentences each). One per line.",
    "review_text": "List 20 realistic customer product reviews (1-2 sentences). One per line.",
    "special_request": "List 20 realistic hotel guest special requests. One per line.",
    "transaction_description": "List 20 realistic bank transaction descriptions (e.g., 'UPI transfer to merchant', 'ATM withdrawal'). One per line.",
    "ticket_description": "List 20 realistic support ticket problem descriptions. One per line.",
    "assignment_description": "List 20 realistic university assignment descriptions. One per line.",
    "delivery_notes": "List 20 realistic food delivery special instructions. One per line.",
    "tour_description": "List 20 realistic travel tour package descriptions (1-2 sentences). One per line.",
}

GENERIC_AI_PROMPT = (
    "List 20 realistic, varied values for a database column named '{col_name}' "
    "in a {domain} application. Keep each value concise (under 20 words). "
    "One value per line, no numbering or bullets."
)


# ---------------------------------------------------------------------------
# AI value cache — avoids repeated API calls for the same column type
# ---------------------------------------------------------------------------

_ai_value_cache: Dict[Tuple[str, str], List[str]] = {}


def _get_ai_values(
    col_name: str,
    domain: str,
    provider: BaseAIProvider,
    count: int = 20,
) -> List[str]:
    """
    Return a list of AI-generated values for the given column.
    Results are cached per (domain, normalised_col_name).
    """
    cache_key = (domain, re.sub(r"[^a-z0-9]", "_", col_name.lower()))

    if cache_key in _ai_value_cache:
        return _ai_value_cache[cache_key]

    # Find the best prompt
    prompt_key = None
    for key in COLUMN_PROMPTS:
        if key in col_name.lower():
            prompt_key = key
            break

    if prompt_key:
        prompt = COLUMN_PROMPTS[prompt_key]
    else:
        prompt = GENERIC_AI_PROMPT.format(col_name=col_name, domain=domain)

    try:
        raw = provider.complete(prompt, max_tokens=1024)
        values = [line.strip() for line in raw.strip().splitlines() if line.strip()]
        # Keep only non-empty, non-numbered lines
        values = [re.sub(r"^\d+[\.\)]\s*", "", v) for v in values if len(v) > 3]
        if not values:
            values = [f"AI-generated {col_name} value {i}" for i in range(count)]
        _ai_value_cache[cache_key] = values
        return values
    except Exception as exc:
        # Fallback values
        fallback = [f"Sample {col_name.replace('_', ' ')} {i+1}" for i in range(count)]
        _ai_value_cache[cache_key] = fallback
        return fallback


def clear_ai_cache():
    """Clear the AI value cache (useful between test runs)."""
    _ai_value_cache.clear()


# ---------------------------------------------------------------------------
# Column AI eligibility check
# ---------------------------------------------------------------------------

def should_use_ai(col: ColumnModel) -> bool:
    """
    Return True if this column should use AI-generated values.
    """
    if col.is_primary_key:
        return False
    dtype = col.data_type.upper()
    if dtype not in AI_ELIGIBLE_TYPES:
        return False
    col_lower = col.name.lower()
    return any(p.search(col_lower) for p in AI_COLUMN_COMPILED)


# ---------------------------------------------------------------------------
# Hybrid table data generator
# ---------------------------------------------------------------------------

def generate_table_data_hybrid(
    table: TableModel,
    num_rows: int,
    column_hints: Dict[str, str],
    parent_data: Dict[str, List[Dict[str, Any]]],
    domain: str,
    provider: BaseAIProvider,
    ai_fields_used: List[str],
    faker_fields_used: List[str],
) -> List[Dict[str, Any]]:
    """
    Generate rows for one table, using AI for semantic fields and Faker for the rest.

    Args:
        table:            TableModel for this table.
        num_rows:         How many rows to generate.
        column_hints:     Faker hints from agent classification.
        parent_data:      Already-generated parent table data (for FK lookups).
        domain:           Selected domain context.
        provider:         AI provider instance.
        ai_fields_used:   Mutable list — appended with AI-generated column names.
        faker_fields_used: Mutable list — appended with Faker-generated column names.

    Returns:
        List of row dicts.
    """
    rows: List[Dict[str, Any]] = []
    unique_trackers: Dict[str, Set] = {
        col.name: set() for col in table.columns if col.is_unique
    }
    pk_counter = 1

    # FK lookup
    fk_lookup: Dict[str, List[Any]] = {}
    for fk in table.foreign_keys:
        parent_rows = parent_data.get(fk.ref_table.lower(), [])
        fk_lookup[fk.column] = [row[fk.ref_column] for row in parent_rows] if parent_rows else []

    # Pre-fetch AI values for AI-eligible columns
    ai_value_pools: Dict[str, List[str]] = {}
    for col in table.columns:
        if should_use_ai(col) and provider.is_available():
            values = _get_ai_values(col.name, domain, provider, count=max(num_rows, 20))
            ai_value_pools[col.name] = values
            full_key = f"{table.name}.{col.name}"
            if full_key not in ai_fields_used:
                ai_fields_used.append(full_key)
        else:
            full_key = f"{table.name}.{col.name}"
            if full_key not in faker_fields_used and not col.is_primary_key:
                faker_fields_used.append(full_key)

    for _ in range(num_rows):
        row: Dict[str, Any] = {}

        for col in table.columns:
            # Primary key
            if col.is_primary_key:
                row[col.name] = pk_counter
                pk_counter += 1
                continue

            # Foreign key
            if col.name in fk_lookup:
                valid_ids = fk_lookup[col.name]
                row[col.name] = random.choice(valid_ids) if valid_ids else 1
                continue

            # Nullable — chance of NULL
            if col.is_nullable and col.default_value is None:
                if random.random() < 0.10:
                    row[col.name] = None
                    continue

            # AI-generated value
            if col.name in ai_value_pools:
                pool = ai_value_pools[col.name]
                value = random.choice(pool) if pool else f"AI {col.name}"
                # Respect UNIQUE constraint
                used = unique_trackers.get(col.name, set())
                if col.is_unique:
                    attempts = 0
                    while value in used and attempts < 50:
                        value = random.choice(pool) if pool else f"AI {col.name} {random.randint(1000, 9999)}"
                        attempts += 1
                    used.add(value)
                # Truncate to max_length
                if col.max_length and isinstance(value, str):
                    value = value[:col.max_length]
                row[col.name] = value
                continue

            # Faker-generated value
            hint = column_hints.get(col.name, "word")
            used = unique_trackers.get(col.name, set())
            value = generate_value_for_hint(hint, col, used)
            if isinstance(value, str) and col.max_length:
                value = value[:col.max_length]
            row[col.name] = value

        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# Top-level hybrid generation function
# ---------------------------------------------------------------------------

def generate_all_data_hybrid(
    schema: SchemaModel,
    generation_order: List[str],
    num_rows: int,
    domain: str = "general",
    provider: Optional[BaseAIProvider] = None,
    agent: Optional[DataGeneratorAgent] = None,
) -> Dict[str, Any]:
    """
    Generate data for all tables using hybrid Faker + AI strategy.

    Returns:
        {
            "data": {table_name: [rows]},
            "faker_generated_fields": [...],
            "ai_generated_fields": [...],
            "generation_mode_used": "hybrid" | "faker_only",
            "provider_used": str,
        }
    """
    if provider is None:
        provider = get_provider()

    # Use agent column hints if available
    column_hints_all: Dict[str, Dict[str, str]] = {}
    if agent and agent.column_hints:
        column_hints_all = agent.column_hints
    else:
        for tname, table in schema.tables.items():
            column_hints_all[tname] = {col.name: classify_column(col) for col in table.columns}

    all_data: Dict[str, List[Dict[str, Any]]] = {}
    ai_fields_used: List[str] = []
    faker_fields_used: List[str] = []

    ai_available = provider.is_available()

    for tname in generation_order:
        table = schema.get_table(tname)
        if table is None:
            continue

        if agent:
            agent.act_start(tname)

        hints = column_hints_all.get(tname, {})

        if ai_available:
            rows = generate_table_data_hybrid(
                table, num_rows, hints, all_data,
                domain, provider, ai_fields_used, faker_fields_used,
            )
        else:
            # Pure Faker fallback — track all non-PK columns as Faker
            rows = generate_table_data(table, num_rows, hints, all_data)
            for col in table.columns:
                if not col.is_primary_key:
                    faker_fields_used.append(f"{tname}.{col.name}")

        all_data[tname] = rows

        if agent:
            agent.act_done(tname, len(rows))

    mode = "hybrid" if (ai_available and ai_fields_used) else "faker_only"

    return {
        "data": all_data,
        "faker_generated_fields": list(dict.fromkeys(faker_fields_used)),
        "ai_generated_fields": list(dict.fromkeys(ai_fields_used)),
        "generation_mode_used": mode,
        "provider_used": provider.provider_name,
    }
