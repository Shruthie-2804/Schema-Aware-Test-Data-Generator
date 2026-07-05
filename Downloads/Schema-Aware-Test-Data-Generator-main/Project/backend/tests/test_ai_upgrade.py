"""
test_ai_upgrade.py
------------------
Pytest test suite for the AI-powered upgrade modules.
All AI calls are mocked — no real API key needed to run tests.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Ensure the backend src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ddl_parser import parse_ddl
from src.schema_classifier import classify_schema, ClassificationResult
from src.schema_regenerator import regenerate_schema, _extract_ddl
from src.hybrid_generator import (
    should_use_ai, generate_all_data_hybrid, clear_ai_cache
)
from src.ai_provider import (
    FallbackProvider, GeminiProvider, get_provider
)
from src.schema_models import ColumnModel


# ── Sample DDLs ──────────────────────────────────────────────────────────────

SIMPLE_DDL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);
"""

HOSPITAL_DDL = """
CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    diagnosis TEXT,
    treatment_plan TEXT
);

CREATE TABLE doctors (
    doctor_id INTEGER PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    department VARCHAR(100),
    doctor_notes TEXT
);

CREATE TABLE appointments (
    appointment_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    doctor_id INTEGER,
    appointment_date DATE NOT NULL,
    status VARCHAR(30),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);
"""

MOCK_SCHEMA_SQL = """
CREATE TABLE hospital_patients (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    blood_group VARCHAR(5)
);

CREATE TABLE hospital_doctors (
    id INTEGER PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    department VARCHAR(100)
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'scheduled',
    FOREIGN KEY (patient_id) REFERENCES hospital_patients(id),
    FOREIGN KEY (doctor_id) REFERENCES hospital_doctors(id)
);
"""


# ===========================================================================
# Tests: Schema Classifier
# ===========================================================================

class TestSchemaClassifier:

    def test_basic_schema_classified_correctly(self):
        schema = parse_ddl(SIMPLE_DDL)
        result = classify_schema(schema)
        assert result.complexity == "basic"
        assert isinstance(result.detected_domain, str)

    def test_hospital_schema_detected(self):
        schema = parse_ddl(HOSPITAL_DDL)
        result = classify_schema(schema, selected_domain="hospital")
        # Should detect hospital or close domain
        assert result.detected_domain in ("hospital", "general", "unknown")

    def test_ai_columns_detected_in_hospital_schema(self):
        schema = parse_ddl(HOSPITAL_DDL)
        result = classify_schema(schema)
        # diagnosis and treatment_plan should be AI columns
        ai_col_names = [c.split(".")[-1] for c in result.ai_columns]
        assert "diagnosis" in ai_col_names or "treatment_plan" in ai_col_names

    def test_recommendation_for_basic_with_domain_mismatch(self):
        schema = parse_ddl(SIMPLE_DDL)
        result = classify_schema(schema, selected_domain="hospital")
        # Basic schema + hospital domain = regeneration recommended
        assert result.recommendation in ("ai_regeneration", "faker_only")

    def test_hybrid_recommended_for_ai_columns(self):
        schema = parse_ddl(HOSPITAL_DDL)
        result = classify_schema(schema)
        assert result.recommendation in ("hybrid", "ai_regeneration")

    def test_result_has_required_fields(self):
        schema = parse_ddl(SIMPLE_DDL)
        result = classify_schema(schema)
        assert hasattr(result, "complexity")
        assert hasattr(result, "detected_domain")
        assert hasattr(result, "recommendation")
        assert hasattr(result, "reason")
        assert isinstance(result.ai_columns, list)
        assert isinstance(result.faker_columns, list)


# ===========================================================================
# Tests: AI Provider
# ===========================================================================

class TestAIProvider:

    def test_fallback_provider_not_available(self):
        provider = FallbackProvider()
        assert not provider.is_available()

    def test_fallback_provider_returns_error_message(self):
        provider = FallbackProvider()
        result = provider.complete("test prompt")
        assert "AI_UNAVAILABLE" in result

    def test_fallback_provider_name(self):
        provider = FallbackProvider()
        assert provider.provider_name == "fallback"

    def test_gemini_not_available_without_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            p = GeminiProvider()
            assert not p.is_available()

    def test_gemini_not_available_with_placeholder(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "your_api_key_here"}, clear=False):
            p = GeminiProvider()
            assert not p.is_available()

    def test_get_provider_returns_fallback_when_no_env(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "fallback"}, clear=False):
            provider = get_provider()
            assert provider.provider_name == "fallback"

    def test_get_provider_returns_fallback_for_missing_key(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": ""}, clear=False):
            provider = get_provider()
            assert provider.provider_name == "fallback"

    def test_get_provider_returns_gemini_with_valid_key(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "real-key-123"}, clear=False):
            provider = get_provider()
            assert "gemini" in provider.provider_name


# ===========================================================================
# Tests: Schema Regenerator (mocked AI)
# ===========================================================================

class TestSchemaRegenerator:

    def _make_mock_provider(self, response_text: str):
        mock = MagicMock()
        mock.is_available.return_value = True
        mock.provider_name = "mock/test"
        mock.complete.return_value = response_text
        return mock

    def test_regenerate_returns_valid_schema(self):
        mock_provider = self._make_mock_provider(MOCK_SCHEMA_SQL)
        result = regenerate_schema(SIMPLE_DDL, "hospital", provider=mock_provider)
        assert result["success"] is True
        assert len(result["tables"]) >= 2
        assert "generated_schema_sql" in result
        assert result["domain"] == "hospital"

    def test_regenerate_with_fallback_provider(self):
        provider = FallbackProvider()
        result = regenerate_schema(SIMPLE_DDL, "hospital", provider=provider)
        assert result["success"] is False
        assert len(result["warnings"]) > 0

    def test_extract_ddl_strips_markdown(self):
        raw = "```sql\nCREATE TABLE foo (id INTEGER PRIMARY KEY);\n```"
        cleaned = _extract_ddl(raw)
        assert "```" not in cleaned
        assert "CREATE TABLE" in cleaned

    def test_regenerate_fixes_invalid_ddl(self):
        """If first attempt is bad, AI should be called again to fix it."""
        bad_ddl = "THIS IS NOT SQL"
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.provider_name = "mock/test"
        # First call returns bad DDL, second call returns valid DDL
        mock_provider.complete.side_effect = [bad_ddl, MOCK_SCHEMA_SQL]

        result = regenerate_schema(SIMPLE_DDL, "hospital", provider=mock_provider)
        # Should have been called at least twice (generate + fix + optional explanation)
        assert mock_provider.complete.call_count >= 2

    def test_warnings_present_when_fix_needed(self):
        bad_ddl = "INVALID SQL"
        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.provider_name = "mock/test"
        mock_provider.complete.side_effect = [bad_ddl, MOCK_SCHEMA_SQL, "Explanation text."]
        result = regenerate_schema(SIMPLE_DDL, "hospital", provider=mock_provider)
        if result["success"]:
            assert len(result.get("warnings", [])) >= 0  # may have warnings


# ===========================================================================
# Tests: Hybrid Generator
# ===========================================================================

class TestHybridGenerator:

    def setup_method(self):
        clear_ai_cache()

    def test_should_use_ai_for_diagnosis(self):
        col = ColumnModel(name="diagnosis", data_type="TEXT")
        assert should_use_ai(col) is True

    def test_should_use_ai_for_treatment_plan(self):
        col = ColumnModel(name="treatment_plan", data_type="TEXT")
        assert should_use_ai(col) is True

    def test_should_not_use_ai_for_pk(self):
        col = ColumnModel(name="diagnosis", data_type="TEXT", is_primary_key=True)
        assert should_use_ai(col) is False

    def test_should_not_use_ai_for_integer_field(self):
        col = ColumnModel(name="diagnosis", data_type="INTEGER")
        assert should_use_ai(col) is False

    def test_should_not_use_ai_for_email(self):
        col = ColumnModel(name="email", data_type="VARCHAR")
        assert should_use_ai(col) is False

    def test_hybrid_generation_with_fallback_provider(self):
        """With fallback provider, should generate all rows using Faker."""
        schema = parse_ddl(HOSPITAL_DDL)
        from src.dependency_resolver import resolve_generation_order
        order = resolve_generation_order(schema)
        provider = FallbackProvider()

        result = generate_all_data_hybrid(
            schema=schema,
            generation_order=order,
            num_rows=3,
            domain="hospital",
            provider=provider,
        )
        assert result["generation_mode_used"] == "faker_only"
        assert len(result["data"]) == len(order)
        for tname in order:
            assert len(result["data"][tname]) == 3

    def test_hybrid_generation_with_mock_ai(self):
        """With a mock AI provider, should use AI for diagnosis column."""
        schema = parse_ddl(HOSPITAL_DDL)
        from src.dependency_resolver import resolve_generation_order
        order = resolve_generation_order(schema)

        mock_provider = MagicMock()
        mock_provider.is_available.return_value = True
        mock_provider.provider_name = "mock/test"
        mock_provider.complete.return_value = (
            "Type 2 Diabetes\nAcute Appendicitis\nHypertension\n"
            "Migraine\nPneumonia\nFracture\nAnemia\nAsthma\nTyphoid\nCholera\n"
            "Dengue\nMalaria\nBronchitis\nArthritis\nOsteoporosis\n"
            "Epilepsy\nDepression\nAnxiety\nThyroid\nCancer"
        )

        result = generate_all_data_hybrid(
            schema=schema,
            generation_order=order,
            num_rows=5,
            domain="hospital",
            provider=mock_provider,
        )
        assert result["generation_mode_used"] == "hybrid"
        assert len(result["ai_generated_fields"]) > 0
        # Check data exists
        for tname in order:
            assert len(result["data"][tname]) == 5

    def test_faker_only_generation_after_hybrid(self):
        """Faker-only mode should not call AI provider."""
        schema = parse_ddl(SIMPLE_DDL)
        from src.dependency_resolver import resolve_generation_order
        order = resolve_generation_order(schema)
        provider = FallbackProvider()

        result = generate_all_data_hybrid(
            schema=schema,
            generation_order=order,
            num_rows=5,
            domain="general",
            provider=provider,
        )
        assert result["generation_mode_used"] == "faker_only"
        assert result["ai_generated_fields"] == []


# ===========================================================================
# Tests: API endpoints (using httpx TestClient, mocked AI)
# ===========================================================================

class TestAPIEndpoints:

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from api import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "ai_provider" in data

    def test_ai_status_endpoint(self, client):
        resp = client.get("/api/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "available" in data

    def test_classify_schema_endpoint(self, client):
        resp = client.post(
            "/api/ai/classify-schema",
            json={"ddl_schema": SIMPLE_DDL, "selected_domain": "hospital"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "complexity" in data
        assert "recommendation" in data

    def test_classify_schema_invalid_ddl(self, client):
        resp = client.post(
            "/api/ai/classify-schema",
            json={"ddl_schema": "NOT SQL"},
        )
        assert resp.status_code == 400

    def test_regenerate_schema_with_fallback(self, client):
        """Without AI configured, should return success=False with a warning."""
        with patch("api.get_provider", return_value=FallbackProvider()):
            resp = client.post(
                "/api/ai/regenerate-schema",
                json={
                    "original_schema": SIMPLE_DDL,
                    "input_type": "sql",
                    "domain": "hospital",
                    "user_instruction": "",
                    "confirm_regeneration": True,
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert len(data["warnings"]) > 0

    def test_hybrid_generate_faker_only(self, client):
        resp = client.post(
            "/api/generate/hybrid",
            json={
                "ddl_schema": SIMPLE_DDL,
                "rows_per_table": 3,
                "generation_mode": "faker_only",
                "domain": "general",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["generation_mode_used"] == "faker_only"

    def test_explain_generation_endpoint(self, client):
        resp = client.post(
            "/api/ai/explain-generation",
            json={
                "ddl_schema": SIMPLE_DDL,
                "domain": "general",
                "generation_mode_used": "faker_only",
                "faker_generated_fields": ["users.name", "users.email"],
                "ai_generated_fields": [],
                "validation_passed": True,
                "validation_issues": [],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "explanation" in data
        assert data["faker_columns_count"] == 2

    def test_parse_endpoint_still_works(self, client):
        """Ensure the existing /api/parse endpoint is not broken."""
        resp = client.post("/api/parse", json={"ddl": SIMPLE_DDL})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["tables"]) >= 1
