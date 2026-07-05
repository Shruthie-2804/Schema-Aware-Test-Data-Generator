"""
dependency_resolver.py
----------------------
Builds a dependency graph from FK relationships and produces a
topologically-sorted table generation order (parents before children).

Uses a simple DFS-based topological sort — no external library required,
though networkx is imported optionally for the visualisation helper.
"""

from typing import Dict, List, Set
from src.schema_models import SchemaModel


class CircularDependencyError(Exception):
    """Raised when the FK graph contains a cycle (which we cannot handle)."""
    pass


def build_dependency_graph(schema: SchemaModel) -> Dict[str, Set[str]]:
    """
    Build an adjacency map:
      { child_table -> {parent_table, ...} }

    Example: orders depends on users  →  {"orders": {"users"}}
    """
    graph: Dict[str, Set[str]] = {name: set() for name in schema.tables}

    for tname, table in schema.tables.items():
        for fk in table.foreign_keys:
            parent = fk.ref_table.lower()
            if parent in graph:
                graph[tname].add(parent)
            else:
                # Referenced table not in schema — warn but continue
                print(f"[WARNING] Table '{parent}' referenced by FK in "
                      f"'{tname}' not found in schema. Skipping dependency.")

    return graph


def topological_sort(graph: Dict[str, Set[str]]) -> List[str]:
    """
    Kahn's algorithm (BFS-based) for topological sort.
    Returns tables ordered so parents always appear before children.

    Raises CircularDependencyError if a cycle is detected.
    """
    # Compute in-degree for each node
    in_degree: Dict[str, int] = {node: 0 for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            if dep in in_degree:
                in_degree[dep] = in_degree.get(dep, 0)  # ensure key exists
            # node depends on dep  →  dep must come first
            # In the reverse sense: dep has no in-dependency from node
            # We track: how many tables must come before each table
    
    # Rebuild: in_degree[t] = number of tables that t depends on
    in_degree = {node: len(deps) for node, deps in graph.items()}

    # Build reverse map: parent → [children that depend on it]
    reverse: Dict[str, List[str]] = {node: [] for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            if dep in reverse:
                reverse[dep].append(node)

    # Start with all tables that have no dependencies (root tables)
    queue = [node for node, deg in in_degree.items() if deg == 0]
    queue.sort()  # deterministic order
    result = []

    while queue:
        node = queue.pop(0)
        result.append(node)
        for child in sorted(reverse.get(node, [])):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(result) != len(graph):
        # Some nodes were never added → cycle detected
        remaining = set(graph.keys()) - set(result)
        raise CircularDependencyError(
            f"Circular FK dependency detected among tables: {remaining}. "
            "Cyclic foreign keys are not supported in this prototype."
        )

    return result


def resolve_generation_order(schema: SchemaModel) -> List[str]:
    """
    Public entry point.
    Returns the list of table names in the order they should be generated,
    ensuring all parent tables come before their child tables.
    """
    graph = build_dependency_graph(schema)
    order = topological_sort(graph)
    return order


def describe_dependencies(schema: SchemaModel) -> str:
    """Return a human-readable description of FK dependencies."""
    lines = ["FK Dependency Graph:\n"]
    for tname, table in schema.tables.items():
        if table.foreign_keys:
            for fk in table.foreign_keys:
                lines.append(f"  {tname}.{fk.column}  ->  {fk.ref_table}.{fk.ref_column}")
    if len(lines) == 1:
        lines.append("  (No foreign key relationships detected)")
    return "\n".join(lines)
