"""
test_dependency_order.py
------------------------
Unit tests for the dependency resolver / topological sort module.

Tests:
  - Root tables (no FKs) come first
  - Child tables come after their parent tables
  - Multi-level dependency chains
  - Circular dependency detection
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ddl_parser import parse_ddl
from src.dependency_resolver import (
    resolve_generation_order,
    build_dependency_graph,
    topological_sort,
    CircularDependencyError,
)


# ---- Fixtures ---------------------------------------------------------------

SIMPLE_DDL = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
"""

MULTI_PARENT_DDL = """
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE purchases (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
"""

NO_FK_DDL = """
CREATE TABLE alpha (id INTEGER PRIMARY KEY, val TEXT);
CREATE TABLE beta  (id INTEGER PRIMARY KEY, val TEXT);
CREATE TABLE gamma (id INTEGER PRIMARY KEY, val TEXT);
"""


# ---- Tests ------------------------------------------------------------------

class TestGenerationOrder:
    def test_parent_before_child_simple(self):
        schema = parse_ddl(SIMPLE_DDL)
        order = resolve_generation_order(schema)
        assert order.index("users") < order.index("orders")
        assert order.index("orders") < order.index("order_items")

    def test_all_tables_included(self):
        schema = parse_ddl(SIMPLE_DDL)
        order = resolve_generation_order(schema)
        assert set(order) == {"users", "orders", "order_items"}

    def test_multi_parent_both_before_child(self):
        schema = parse_ddl(MULTI_PARENT_DDL)
        order = resolve_generation_order(schema)
        assert order.index("products") < order.index("purchases")
        assert order.index("customers") < order.index("purchases")

    def test_no_fk_tables_all_included(self):
        schema = parse_ddl(NO_FK_DDL)
        order = resolve_generation_order(schema)
        assert set(order) == {"alpha", "beta", "gamma"}
        assert len(order) == 3

    def test_single_table(self):
        ddl = "CREATE TABLE solo (id INTEGER PRIMARY KEY, name TEXT);"
        schema = parse_ddl(ddl)
        order = resolve_generation_order(schema)
        assert order == ["solo"]


class TestDependencyGraph:
    def test_graph_structure(self):
        schema = parse_ddl(SIMPLE_DDL)
        graph = build_dependency_graph(schema)
        # orders depends on users
        assert "users" in graph["orders"]
        # order_items depends on orders
        assert "orders" in graph["order_items"]
        # users has no dependencies
        assert len(graph["users"]) == 0

    def test_multi_fk_graph(self):
        schema = parse_ddl(MULTI_PARENT_DDL)
        graph = build_dependency_graph(schema)
        assert "products" in graph["purchases"]
        assert "customers" in graph["purchases"]


class TestTopologicalSort:
    def test_simple_chain(self):
        graph = {"a": set(), "b": {"a"}, "c": {"b"}}
        order = topological_sort(graph)
        assert order.index("a") < order.index("b") < order.index("c")

    def test_no_edges(self):
        graph = {"x": set(), "y": set(), "z": set()}
        order = topological_sort(graph)
        assert set(order) == {"x", "y", "z"}

    def test_circular_raises(self):
        # a → b → a  (cycle)
        graph = {"a": {"b"}, "b": {"a"}}
        with pytest.raises(CircularDependencyError):
            topological_sort(graph)
