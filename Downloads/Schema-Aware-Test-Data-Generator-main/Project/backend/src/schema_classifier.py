"""
schema_classifier.py
---------------------
Analyses an input schema and classifies:
  - Complexity level: basic | medium | high | domain_specific
  - Detected domain: hospital | ecommerce | hospitality | banking | education |
                     inventory | crm | food_delivery | travel | general | unknown
  - Recommended generation mode: faker_only | hybrid | ai_regeneration

The classifier uses keyword matching on table names and column names — no AI call
needed, keeping it fast and free.

Used by the agent loop (ANALYSE step) and the /api/ai/classify-schema endpoint.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.schema_models import SchemaModel


# ---------------------------------------------------------------------------
# Domain keyword maps — {domain_id: [keyword patterns]}
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "hospital": [
        "patient", "doctor", "physician", "nurse", "diagnosis", "prescription",
        "appointment", "ward", "clinic", "medical", "treatment", "medication",
        "surgery", "lab_result", "radiology", "insurance_claim", "billing",
        "department", "bed", "room", "emergency", "outpatient", "inpatient",
    ],
    "ecommerce": [
        "product", "order", "cart", "checkout", "payment", "shipment", "delivery",
        "customer", "review", "rating", "category", "inventory", "discount",
        "coupon", "wishlist", "seller", "marketplace", "sku", "warehouse",
    ],
    "hospitality": [
        "hotel", "room", "booking", "reservation", "guest", "checkin", "checkout",
        "amenity", "housekeeping", "concierge", "reception", "suite", "tariff",
        "occupancy", "folio", "front_desk",
    ],
    "banking": [
        "account", "transaction", "ledger", "loan", "credit", "debit", "balance",
        "branch", "atm", "ifsc", "swift", "upi", "neft", "rtgs", "interest",
        "emi", "mortgage", "deposit", "withdrawal", "bank", "finance",
    ],
    "education": [
        "student", "teacher", "course", "enrollment", "grade", "marks", "exam",
        "assignment", "attendance", "semester", "class", "lecture", "curriculum",
        "faculty", "university", "college", "school", "gpa", "transcript",
    ],
    "inventory": [
        "stock", "warehouse", "supplier", "purchase_order", "item", "sku",
        "shelf", "bin", "reorder", "lead_time", "rop", "minimum_stock",
        "batch", "expiry", "serial_number", "asset",
    ],
    "crm": [
        "lead", "opportunity", "pipeline", "deal", "contact", "campaign",
        "followup", "ticket", "support", "agent", "sla", "feedback", "survey",
        "retention", "churn", "lifecycle",
    ],
    "food_delivery": [
        "restaurant", "menu", "dish", "cuisine", "delivery", "rider", "order",
        "rating", "review", "outlet", "kitchen", "coupon", "zone", "slot",
        "pickup", "driver", "eta",
    ],
    "travel": [
        "flight", "airline", "booking", "itinerary", "passenger", "seat",
        "hotel", "tour", "package", "visa", "passport", "check_in", "boarding",
        "route", "destination", "terminal", "pnr",
    ],
}

# High-level / domain-specific column keywords that benefit from AI generation
AI_COLUMN_KEYWORDS = [
    "diagnosis", "prescription", "treatment_plan", "clinical_notes",
    "doctor_notes", "medical_history", "lab_results",
    "product_description", "review", "feedback", "comments",
    "hotel_special_request", "room_notes", "concierge_request",
    "transaction_description", "transaction_notes", "remarks",
    "support_description", "ticket_description", "issue_details",
    "course_feedback", "assignment_description", "lecture_notes",
    "lead_notes", "opportunity_notes", "deal_description",
    "order_special_instructions", "delivery_notes",
    "travel_notes", "itinerary_details", "tour_description",
]

# Simple columns that are always well-served by Faker
SIMPLE_COLUMN_KEYWORDS = [
    "name", "email", "phone", "address", "city", "state", "country",
    "zip", "postal", "id", "created_at", "updated_at", "date",
    "price", "amount", "status", "gender", "age", "dob",
    "username", "password", "url", "image", "rating",
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    complexity: str          # basic | medium | high | domain_specific
    detected_domain: str     # hospital | ecommerce | ... | general | unknown
    recommendation: str      # faker_only | hybrid | ai_regeneration
    reason: str
    domain_score: Dict[str, int]   # raw scores for each domain
    ai_columns: List[str]          # columns that should use AI
    faker_columns: List[str]       # columns that can use Faker


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def classify_schema(schema: SchemaModel, selected_domain: Optional[str] = None) -> ClassificationResult:
    """
    Classify the schema and return a ClassificationResult.

    Args:
        schema:          Parsed SchemaModel.
        selected_domain: Domain the user selected in the UI (optional).

    Returns:
        ClassificationResult with complexity, domain, recommendation, and column lists.
    """
    all_tokens: List[str] = []  # table names + column names, normalised
    for tname, table in schema.tables.items():
        all_tokens.append(tname.lower())
        for col in table.columns:
            all_tokens.append(col.name.lower())

    # ---- Score each domain ------------------------------------------------
    domain_scores: Dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for token in all_tokens:
            for kw in keywords:
                if kw in token or token in kw:
                    score += 1
        domain_scores[domain] = score

    best_domain = max(domain_scores, key=domain_scores.get)  # type: ignore
    best_score = domain_scores[best_domain]

    if best_score == 0:
        detected_domain = "general"
    elif best_score < 3:
        detected_domain = "unknown"
    else:
        detected_domain = best_domain

    # ---- Complexity --------------------------------------------------------
    n_tables = len(schema.tables)
    n_columns = sum(len(t.columns) for t in schema.tables.values())
    n_fks = sum(len(t.foreign_keys) for t in schema.tables.values())

    if n_tables <= 1 and n_columns <= 5:
        complexity = "basic"
    elif n_tables <= 3 and n_fks == 0:
        complexity = "medium"
    elif n_tables >= 5 or n_fks >= 3:
        complexity = "domain_specific"
    else:
        complexity = "high"

    # ---- Identify AI vs Faker columns -------------------------------------
    ai_columns: List[str] = []
    faker_columns: List[str] = []
    for tname, table in schema.tables.items():
        for col in table.columns:
            col_lower = col.name.lower()
            is_ai = any(kw in col_lower for kw in AI_COLUMN_KEYWORDS)
            is_simple = any(kw in col_lower for kw in SIMPLE_COLUMN_KEYWORDS)
            if is_ai and not col.is_primary_key:
                ai_columns.append(f"{tname}.{col.name}")
            else:
                faker_columns.append(f"{tname}.{col.name}")

    # ---- Recommendation logic ---------------------------------------------
    domain_mismatch = (
        selected_domain
        and selected_domain not in ("general", "unknown", "custom")
        and detected_domain not in (selected_domain, "general", "unknown")
        and best_score < 2
    )

    if complexity == "basic" and domain_mismatch:
        recommendation = "ai_regeneration"
        reason = (
            f"Schema is basic ({n_tables} table(s), {n_columns} columns) and does not "
            f"match the selected domain '{selected_domain}'. AI regeneration is recommended "
            f"to create a complete {selected_domain} schema."
        )
    elif len(ai_columns) > 0:
        recommendation = "hybrid"
        reason = (
            f"{len(ai_columns)} column(s) detected as domain-specific semantic fields "
            f"({', '.join(ai_columns[:3])}{'...' if len(ai_columns) > 3 else ''}). "
            f"Hybrid Faker + AI generation recommended."
        )
    elif complexity == "basic":
        recommendation = "faker_only"
        reason = (
            f"Schema is simple ({n_tables} table(s), {n_columns} columns, "
            f"{n_fks} FK(s)). Faker-only generation is sufficient."
        )
    else:
        recommendation = "hybrid"
        reason = (
            f"Schema has {n_tables} table(s) and {n_fks} FK relationships. "
            f"Hybrid generation recommended for realism."
        )

    return ClassificationResult(
        complexity=complexity,
        detected_domain=detected_domain,
        recommendation=recommendation,
        reason=reason,
        domain_score=domain_scores,
        ai_columns=ai_columns,
        faker_columns=faker_columns,
    )
