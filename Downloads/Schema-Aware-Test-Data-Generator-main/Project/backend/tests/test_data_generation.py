"""
test_data_generation.py
-----------------------
Unit tests for the data generator module.

Tests:
  - Correct number of rows generated per table
  - Primary key values are unique
  - NOT NULL columns always have values
  - Agent column classification returns expected hints
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ddl_parser import parse_ddl
from src.dependency_resolver import resolve_generation_order
from src.agent import DataGeneratorAgent, classify_column
from src.schema_models import ColumnModel
from src.data_generator import generate_all_data


SAMPLE_DDL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(50),
    created_at DATETIME
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(50)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(30),
    total_amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


@pytest.fixture(scope="module")
def generated():
    """Run the full generation pipeline once and share results."""
    schema = parse_ddl(SAMPLE_DDL)
    order = resolve_generation_order(schema)
    agent = DataGeneratorAgent(schema, num_rows=10)
    agent.observe()
    agent.think()
    agent.plan(order)
    data = generate_all_data(schema, order, 10, agent)
    return schema, order, data


class TestRowCounts:
    def test_users_row_count(self, generated):
        _, _, data = generated
        assert len(data["users"]) == 10

    def test_products_row_count(self, generated):
        _, _, data = generated
        assert len(data["products"]) == 10

    def test_orders_row_count(self, generated):
        _, _, data = generated
        assert len(data["orders"]) == 10

    def test_custom_row_count(self):
        schema = parse_ddl("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT);")
        order = resolve_generation_order(schema)
        data = generate_all_data(schema, order, 25)
        assert len(data["t"]) == 25


class TestPrimaryKeys:
    def test_pk_uniqueness_users(self, generated):
        _, _, data = generated
        ids = [row["id"] for row in data["users"]]
        assert len(ids) == len(set(ids)), "Duplicate PKs detected in users"

    def test_pk_uniqueness_products(self, generated):
        _, _, data = generated
        ids = [row["id"] for row in data["products"]]
        assert len(ids) == len(set(ids))

    def test_pk_starts_at_1(self, generated):
        _, _, data = generated
        assert data["users"][0]["id"] == 1

    def test_pk_sequential(self, generated):
        _, _, data = generated
        ids = [row["id"] for row in data["users"]]
        assert ids == list(range(1, 11))


class TestNotNull:
    def test_name_not_null(self, generated):
        _, _, data = generated
        for row in data["users"]:
            assert row["name"] is not None

    def test_email_not_null(self, generated):
        _, _, data = generated
        for row in data["users"]:
            assert row["email"] is not None

    def test_price_not_null(self, generated):
        _, _, data = generated
        for row in data["products"]:
            assert row["price"] is not None


class TestUniqueColumns:
    def test_email_uniqueness(self, generated):
        _, _, data = generated
        emails = [row["email"] for row in data["users"]]
        assert len(emails) == len(set(emails)), "Duplicate emails detected"


class TestAgentClassification:
    def test_email_hint(self):
        col = ColumnModel(name="email", data_type="VARCHAR")
        assert classify_column(col) == "email"

    def test_phone_hint(self):
        col = ColumnModel(name="phone", data_type="VARCHAR")
        assert classify_column(col) == "phone_number"

    def test_status_hint(self):
        col = ColumnModel(name="status", data_type="VARCHAR")
        assert classify_column(col) == "status"

    def test_created_at_hint(self):
        col = ColumnModel(name="created_at", data_type="DATETIME")
        assert classify_column(col) == "datetime_recent"

    def test_price_hint(self):
        col = ColumnModel(name="price", data_type="DECIMAL")
        assert classify_column(col) == "decimal_amount"

    def test_pk_hint(self):
        col = ColumnModel(name="id", data_type="INTEGER", is_primary_key=True)
        assert classify_column(col) == "primary_key"

    def test_city_hint(self):
        col = ColumnModel(name="city", data_type="VARCHAR")
        assert classify_column(col) == "city"

    def test_department_hint(self):
        col = ColumnModel(name="department", data_type="VARCHAR")
        assert classify_column(col) == "department"
