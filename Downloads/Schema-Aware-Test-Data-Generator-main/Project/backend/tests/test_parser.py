"""
test_parser.py
--------------
Unit tests for the DDL parser module.

Tests:
  - Correct number of tables extracted
  - Column names and types detected
  - PRIMARY KEY detection
  - FOREIGN KEY detection
  - NOT NULL / UNIQUE constraint detection
  - Error on invalid DDL
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ddl_parser import parse_ddl


# ---- Fixtures ---------------------------------------------------------------

SIMPLE_DDL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(50)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    status VARCHAR(30),
    total DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

FK_DDL = """
CREATE TABLE parent (
    id INTEGER PRIMARY KEY,
    label VARCHAR(50) NOT NULL
);

CREATE TABLE child (
    id INTEGER PRIMARY KEY,
    parent_id INTEGER NOT NULL,
    value TEXT,
    FOREIGN KEY (parent_id) REFERENCES parent(id)
);
"""

INVALID_DDL = "SELECT * FROM nowhere;"


# ---- Tests ------------------------------------------------------------------

class TestTableDetection:
    def test_correct_table_count(self):
        schema = parse_ddl(SIMPLE_DDL)
        assert len(schema.tables) == 2

    def test_table_names_lowercase(self):
        schema = parse_ddl(SIMPLE_DDL)
        assert "users" in schema.tables
        assert "orders" in schema.tables

    def test_column_count_users(self):
        schema = parse_ddl(SIMPLE_DDL)
        table = schema.get_table("users")
        assert table is not None
        assert len(table.columns) == 5

    def test_column_count_orders(self):
        schema = parse_ddl(SIMPLE_DDL)
        table = schema.get_table("orders")
        # FK clause is not a column
        assert len(table.columns) == 4


class TestColumnAttributes:
    def test_primary_key_detected(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        pk_cols = users.get_primary_keys()
        assert "id" in pk_cols

    def test_primary_key_not_nullable(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        id_col = users.get_column("id")
        assert id_col.is_nullable is False

    def test_unique_constraint_detected(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        email_col = users.get_column("email")
        assert email_col.is_unique is True

    def test_not_null_detected(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        name_col = users.get_column("name")
        assert name_col.is_nullable is False

    def test_nullable_column(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        phone_col = users.get_column("phone")
        assert phone_col.is_nullable is True

    def test_varchar_max_length(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        name_col = users.get_column("name")
        assert name_col.max_length == 100

    def test_data_type_normalisation(self):
        schema = parse_ddl(SIMPLE_DDL)
        users = schema.get_table("users")
        id_col = users.get_column("id")
        assert id_col.data_type == "INTEGER"


class TestForeignKeyDetection:
    def test_fk_count(self):
        schema = parse_ddl(SIMPLE_DDL)
        orders = schema.get_table("orders")
        assert len(orders.foreign_keys) == 1

    def test_fk_attributes(self):
        schema = parse_ddl(FK_DDL)
        child = schema.get_table("child")
        fk = child.foreign_keys[0]
        assert fk.column == "parent_id"
        assert fk.ref_table == "parent"
        assert fk.ref_column == "id"

    def test_no_fk_on_parent(self):
        schema = parse_ddl(FK_DDL)
        parent = schema.get_table("parent")
        assert len(parent.foreign_keys) == 0


class TestEdgeCases:
    def test_invalid_ddl_raises(self):
        with pytest.raises(ValueError):
            parse_ddl(INVALID_DDL)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_ddl("")

    def test_comments_stripped(self):
        ddl_with_comments = """
        -- This is a comment
        CREATE TABLE t1 (
            id INTEGER PRIMARY KEY, -- inline comment
            val VARCHAR(50) NOT NULL
        );
        """
        schema = parse_ddl(ddl_with_comments)
        assert "t1" in schema.tables
        assert len(schema.get_table("t1").columns) == 2

    def test_multiple_fks(self):
        ddl = """
        CREATE TABLE a (id INTEGER PRIMARY KEY, x VARCHAR(10));
        CREATE TABLE b (id INTEGER PRIMARY KEY, y VARCHAR(10));
        CREATE TABLE c (
            id INTEGER PRIMARY KEY,
            a_id INTEGER NOT NULL,
            b_id INTEGER NOT NULL,
            FOREIGN KEY (a_id) REFERENCES a(id),
            FOREIGN KEY (b_id) REFERENCES b(id)
        );
        """
        schema = parse_ddl(ddl)
        c = schema.get_table("c")
        assert len(c.foreign_keys) == 2
