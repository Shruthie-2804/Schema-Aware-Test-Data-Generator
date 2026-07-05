"""
test_fk_validation.py
---------------------
Unit tests for the FK validation module.

Tests:
  - FK validation passes for correctly generated data
  - PK uniqueness validation passes
  - NOT NULL validation passes
  - Validation correctly detects injected FK violations
  - Row count validation
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ddl_parser import parse_ddl
from src.dependency_resolver import resolve_generation_order
from src.agent import DataGeneratorAgent
from src.data_generator import generate_all_data
from src.validators import (
    run_all_validations,
    validate_primary_keys,
    validate_foreign_keys,
    validate_not_null,
    validate_row_counts,
)


FK_DDL = """
CREATE TABLE parents (
    id INTEGER PRIMARY KEY,
    label VARCHAR(50) NOT NULL
);

CREATE TABLE children (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY (parent_id) REFERENCES parents(id)
);
"""

ECOMMERCE_DDL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(30),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


@pytest.fixture(scope="module")
def ecommerce_data():
    schema = parse_ddl(ECOMMERCE_DDL)
    order = resolve_generation_order(schema)
    data = generate_all_data(schema, order, 10)
    return schema, data


@pytest.fixture(scope="module")
def fk_data():
    schema = parse_ddl(FK_DDL)
    order = resolve_generation_order(schema)
    data = generate_all_data(schema, order, 5)
    return schema, data


class TestFullValidationPasses:
    def test_ecommerce_passes(self, ecommerce_data):
        schema, data = ecommerce_data
        passed, issues = run_all_validations(schema, data, 10)
        assert passed, f"Validation failed with issues: {issues}"

    def test_fk_schema_passes(self, fk_data):
        schema, data = fk_data
        passed, issues = run_all_validations(schema, data, 5)
        assert passed, f"Validation failed: {issues}"


class TestPKValidation:
    def test_unique_pks_pass(self):
        rows = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}, {"id": 3, "val": "c"}]
        issues = validate_primary_keys("test_table", rows, ["id"])
        assert issues == []

    def test_duplicate_pks_detected(self):
        rows = [{"id": 1, "val": "a"}, {"id": 1, "val": "b"}]  # duplicate id=1
        issues = validate_primary_keys("test_table", rows, ["id"])
        assert len(issues) > 0
        assert "Duplicate primary key" in issues[0]

    def test_no_pk_columns_no_issues(self):
        rows = [{"val": "a"}, {"val": "b"}]
        issues = validate_primary_keys("no_pk_table", rows, [])
        assert issues == []


class TestFKValidation:
    def test_valid_fks_no_issues(self, ecommerce_data):
        schema, data = ecommerce_data
        issues = validate_foreign_keys(schema, data)
        assert issues == [], f"Unexpected FK issues: {issues}"

    def test_invalid_fk_detected(self, ecommerce_data):
        schema, data = ecommerce_data
        # Inject a bad FK reference
        bad_data = dict(data)
        bad_orders = list(data["orders"])
        bad_orders.append({
            "id": 999,
            "user_id": 99999,  # does not exist in users
            "status": "active",
        })
        bad_data["orders"] = bad_orders
        issues = validate_foreign_keys(schema, bad_data)
        assert any("99999" in i for i in issues), \
            f"Expected FK violation not detected. Issues: {issues}"


class TestNotNullValidation:
    def test_valid_data_passes(self, ecommerce_data):
        schema, data = ecommerce_data
        issues = validate_not_null(schema, data)
        assert issues == []

    def test_null_in_not_null_column_detected(self, ecommerce_data):
        schema, data = ecommerce_data
        bad_data = dict(data)
        bad_users = [dict(row) for row in data["users"]]
        bad_users[0]["name"] = None  # name is NOT NULL
        bad_data["users"] = bad_users
        issues = validate_not_null(schema, bad_data)
        assert any("name" in i for i in issues)


class TestRowCountValidation:
    def test_correct_counts_pass(self, ecommerce_data):
        _, data = ecommerce_data
        issues = validate_row_counts(data, 10)
        assert issues == []

    def test_wrong_count_detected(self, ecommerce_data):
        _, data = ecommerce_data
        issues = validate_row_counts(data, 999)
        assert len(issues) > 0
        assert "Expected 999 rows" in issues[0]
