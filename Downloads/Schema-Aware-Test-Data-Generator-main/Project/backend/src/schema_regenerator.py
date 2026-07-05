"""
schema_regenerator.py
---------------------
Uses an AI provider to regenerate or enhance a user-provided schema
for a specific domain/use-case.

Flow:
  1. Take original schema DDL, selected domain, and optional user instructions.
  2. Build a structured prompt for the AI provider.
  3. Parse the AI response to extract SQL DDL.
  4. Validate the DDL using the existing ddl_parser.
  5. If invalid, ask the AI to fix it once.
  6. Return the result (SQL DDL + explanation + table list).

Domain templates:
  - Each domain has a curated prompt that tells the AI what tables and
    relationships to create.
  - The AI is instructed to return ONLY valid SQL DDL.
"""

import re
import json
import logging
from typing import Optional, List, Dict, Any

from src.ai_provider import BaseAIProvider, get_provider
from src.ddl_parser import parse_ddl

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain prompts — describe what a good schema looks like per domain
# ---------------------------------------------------------------------------

DOMAIN_CONTEXT: Dict[str, str] = {
    "hospital": (
        "Create a complete Hospital Management System schema. Include these tables: "
        "patients (patient details, DOB, blood_group, contact), doctors (specialization, "
        "department), departments (department_name, head_doctor), appointments "
        "(patient_id FK, doctor_id FK, appointment_date, status), prescriptions "
        "(appointment_id FK, medication, dosage, duration), billing (appointment_id FK, "
        "total_amount, payment_status, payment_method), rooms (room_type, floor, capacity, "
        "status), medical_records (patient_id FK, doctor_id FK, diagnosis, treatment_plan, "
        "clinical_notes)."
    ),
    "ecommerce": (
        "Create a complete E-Commerce platform schema. Include: customers (profile, loyalty_points), "
        "products (sku, price, stock_quantity, category), categories (hierarchy), orders "
        "(customer_id FK, total_amount, status), order_items (order_id FK, product_id FK, "
        "quantity, unit_price), payments (order_id FK, payment_method, status, transaction_id), "
        "shipping (order_id FK, address, carrier, tracking_number, delivered_at), "
        "product_reviews (product_id FK, customer_id FK, rating, review_text)."
    ),
    "hospitality": (
        "Create a complete Hotel / Hospitality Management schema. Include: guests (profile, "
        "loyalty_tier), rooms (room_type, floor, rate_per_night, status, amenities), "
        "bookings (guest_id FK, room_id FK, check_in, check_out, total_amount, "
        "special_requests, status), staff (role, department, shift), "
        "services (service_name, price), service_orders (booking_id FK, service_id FK, "
        "quantity, notes), billing (booking_id FK, amount, payment_method, settled_at)."
    ),
    "banking": (
        "Create a complete Banking / Finance schema. Include: customers (profile, kyc_status), "
        "accounts (customer_id FK, account_type, balance, ifsc, status), "
        "transactions (account_id FK, type, amount, description, reference_no, status), "
        "loans (customer_id FK, loan_type, principal, interest_rate, tenure, emi_amount, "
        "status), loan_payments (loan_id FK, paid_amount, paid_at, payment_mode), "
        "cards (account_id FK, card_type, card_number_masked, expiry, status), "
        "branches (name, city, ifsc_prefix, manager_id)."
    ),
    "education": (
        "Create a complete Education / Student Management schema. Include: students "
        "(name, email, dob, enrollment_no, program), teachers (name, email, department, "
        "qualification), courses (course_code, title, credits, department), "
        "enrollments (student_id FK, course_id FK, semester, grade, attendance_pct), "
        "assignments (course_id FK, title, description, due_date, max_marks), "
        "submissions (assignment_id FK, student_id FK, submitted_at, marks_obtained, feedback), "
        "exams (course_id FK, exam_date, max_marks, type), "
        "exam_results (exam_id FK, student_id FK, marks_obtained, grade)."
    ),
    "inventory": (
        "Create a complete Inventory Management schema. Include: products (sku, name, "
        "category, unit_of_measure), suppliers (name, contact, payment_terms), "
        "warehouses (name, location, capacity), stock_levels (product_id FK, warehouse_id FK, "
        "quantity_on_hand, reorder_point, min_stock), purchase_orders (supplier_id FK, "
        "warehouse_id FK, status, expected_delivery), purchase_order_items (po_id FK, "
        "product_id FK, quantity, unit_price), stock_movements (product_id FK, "
        "warehouse_id FK, movement_type, quantity, reason, moved_at)."
    ),
    "crm": (
        "Create a complete CRM / Customer Management schema. Include: contacts (name, "
        "email, phone, company, source), leads (contact_id FK, status, score, assigned_to), "
        "opportunities (lead_id FK, title, value, stage, expected_close), "
        "activities (opportunity_id FK, type, notes, due_at, completed_at), "
        "campaigns (name, channel, budget, start_date, end_date, status), "
        "campaign_contacts (campaign_id FK, contact_id FK, response, converted), "
        "support_tickets (contact_id FK, subject, description, priority, status, resolved_at)."
    ),
    "food_delivery": (
        "Create a complete Food Delivery platform schema. Include: customers (profile, "
        "delivery_address), restaurants (name, cuisine_type, rating, status), "
        "menu_items (restaurant_id FK, name, description, price, category, is_available), "
        "orders (customer_id FK, restaurant_id FK, delivery_address, total_amount, "
        "status, special_instructions), order_items (order_id FK, menu_item_id FK, "
        "quantity, unit_price), delivery_agents (name, phone, vehicle_type, rating, status), "
        "deliveries (order_id FK, agent_id FK, picked_at, delivered_at, rating, notes)."
    ),
    "travel": (
        "Create a complete Travel Booking platform schema. Include: customers (profile, "
        "passport_number), flights (airline, origin, destination, departure_at, arrival_at, "
        "seats_available, price), bookings (customer_id FK, total_amount, status, booked_at), "
        "booking_flights (booking_id FK, flight_id FK, seat_class, seat_number, "
        "passenger_name), hotels (name, city, rating, address), hotel_bookings "
        "(booking_id FK, hotel_id FK, check_in, check_out, room_type, nights, total_cost), "
        "tour_packages (name, destination, duration_days, price, description, includes), "
        "package_bookings (booking_id FK, package_id FK, group_size, notes)."
    ),
    "general": (
        "Create a well-structured relational database schema based on the user's original schema. "
        "Expand it with additional relevant tables, proper foreign keys, constraints, and "
        "realistic column types."
    ),
}


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_regeneration_prompt(
    original_ddl: str,
    domain: str,
    user_instruction: str = "",
) -> str:
    domain_context = DOMAIN_CONTEXT.get(domain, DOMAIN_CONTEXT["general"])
    instruction_block = (
        f"\nAdditional user instruction: {user_instruction.strip()}"
        if user_instruction.strip()
        else ""
    )

    return f"""You are a senior database architect. Generate a complete, production-quality SQL DDL schema.

DOMAIN: {domain.upper()}
{domain_context}

ORIGINAL SCHEMA (user provided, use as context):
```sql
{original_ddl}
```
{instruction_block}

REQUIREMENTS:
1. Return ONLY valid SQL DDL — no explanations, no markdown fences, no comments outside SQL.
2. Use standard SQL (compatible with PostgreSQL and MySQL).
3. Every table must have a PRIMARY KEY.
4. All FOREIGN KEY relationships must be explicit and correct.
5. Include appropriate NOT NULL, UNIQUE, and DEFAULT constraints.
6. Use realistic column names and types.
7. Include at least 6-10 tables with proper relational structure.
8. Ensure tables are ordered so parent tables come before child tables.
9. End every CREATE TABLE statement with a semicolon.

Return ONLY the SQL DDL:"""


def _build_fix_prompt(broken_ddl: str, error_message: str) -> str:
    return f"""The following SQL DDL has a syntax error. Please fix it.

ERROR: {error_message}

BROKEN DDL:
```sql
{broken_ddl}
```

Return ONLY the corrected SQL DDL with no explanations or markdown fences:"""


def _build_explanation_prompt(ddl: str, domain: str) -> str:
    return f"""Briefly explain this {domain} database schema in 3-5 sentences.
Focus on the main tables, their relationships, and what business workflow they support.
Keep it concise and non-technical enough for a stakeholder to understand.

SQL Schema:
```sql
{ddl}
```

Explanation:"""


# ---------------------------------------------------------------------------
# DDL extractor — strips markdown fences if AI wrapped the SQL
# ---------------------------------------------------------------------------

def _extract_ddl(raw: str) -> str:
    """Remove markdown code fences and extract just the SQL."""
    # Remove ```sql ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:sql)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Main regenerator function
# ---------------------------------------------------------------------------

def regenerate_schema(
    original_ddl: str,
    domain: str,
    user_instruction: str = "",
    provider: Optional[BaseAIProvider] = None,
) -> Dict[str, Any]:
    """
    Regenerate or improve the user's schema for the given domain using AI.

    Args:
        original_ddl:      Original DDL from the user (context for AI).
        domain:            Target domain (hospital, ecommerce, etc.).
        user_instruction:  Optional extra instruction from the user.
        provider:          AI provider instance (uses get_provider() if None).

    Returns:
        {
            "success": bool,
            "domain": str,
            "generated_schema_sql": str,
            "explanation": str,
            "tables": [str],
            "warnings": [str],
            "provider_used": str,
        }
    """
    if provider is None:
        provider = get_provider()

    warnings: List[str] = []

    # ---- Check AI availability -------------------------------------------
    if not provider.is_available():
        return {
            "success": False,
            "domain": domain,
            "generated_schema_sql": "",
            "explanation": "",
            "tables": [],
            "warnings": [
                "AI provider is not configured. Set AI_PROVIDER and the corresponding "
                "API key in your .env file. You can continue with your original schema."
            ],
            "provider_used": provider.provider_name,
        }

    # ---- Attempt AI generation -------------------------------------------
    prompt = _build_regeneration_prompt(original_ddl, domain, user_instruction)

    try:
        raw_response = provider.complete(prompt, max_tokens=4096)
    except Exception as exc:
        return {
            "success": False,
            "domain": domain,
            "generated_schema_sql": "",
            "explanation": "",
            "tables": [],
            "warnings": [f"AI generation failed: {exc}"],
            "provider_used": provider.provider_name,
        }

    generated_ddl = _extract_ddl(raw_response)

    # ---- Validate the generated DDL --------------------------------------
    try:
        parsed = parse_ddl(generated_ddl)
        table_names = list(parsed.tables.keys())
    except Exception as parse_error:
        # First-attempt fix
        warnings.append(
            f"First AI attempt produced invalid DDL ({parse_error}). Asking AI to fix..."
        )
        fix_prompt = _build_fix_prompt(generated_ddl, str(parse_error))
        try:
            fixed_raw = provider.complete(fix_prompt, max_tokens=4096)
            generated_ddl = _extract_ddl(fixed_raw)
            parsed = parse_ddl(generated_ddl)
            table_names = list(parsed.tables.keys())
        except Exception as fix_error:
            return {
                "success": False,
                "domain": domain,
                "generated_schema_sql": generated_ddl,
                "explanation": "",
                "tables": [],
                "warnings": warnings + [
                    f"AI fix attempt also failed: {fix_error}. "
                    "Please use your original schema or try again."
                ],
                "provider_used": provider.provider_name,
            }

    # ---- Generate explanation --------------------------------------------
    explanation = ""
    try:
        exp_prompt = _build_explanation_prompt(generated_ddl, domain)
        explanation = provider.complete(exp_prompt, max_tokens=512).strip()
    except Exception:
        explanation = (
            f"AI-generated {domain} schema with {len(table_names)} tables: "
            f"{', '.join(table_names[:5])}."
        )

    return {
        "success": True,
        "domain": domain,
        "generated_schema_sql": generated_ddl,
        "explanation": explanation,
        "tables": table_names,
        "warnings": warnings,
        "provider_used": provider.provider_name,
    }
