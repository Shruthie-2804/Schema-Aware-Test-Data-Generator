from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Backend is running" in data["message"]
    # v2: also has ai_provider and ai_available
    assert "ai_provider" in data
    assert "ai_available" in data

def test_parse_schema():
    ddl = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );
    """
    response = client.post("/api/parse", json={"ddl": ddl})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["tables"]) == 1
    assert data["tables"][0]["name"] == "users"

def test_generate_data():
    ddl = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );
    """
    response = client.post("/api/generate", json={"ddl": ddl, "num_rows": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "users" in data["all_data"]
    assert len(data["all_data"]["users"]) == 5
    assert data["passed"] is True

def test_invalid_schema_returns_400():
    """Sending garbage SQL should return HTTP 400 with an error detail."""
    response = client.post("/api/parse", json={"ddl": "THIS IS NOT SQL AT ALL"})
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

def test_ai_explain_schema():
    ddl = """
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        price DECIMAL(10,2) NOT NULL
    );
    """
    response = client.post("/api/ai/explain-schema", json={"ddl": ddl})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "explanation" in data
    assert len(data["explanation"]) > 10

def test_fk_relationship_generation():
    """Foreign key references should produce valid child rows."""
    ddl = """
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY,
        name VARCHAR(60) NOT NULL
    );
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        category_id INTEGER REFERENCES categories(id),
        name VARCHAR(120) NOT NULL
    );
    """
    response = client.post("/api/generate", json={"ddl": ddl, "num_rows": 3})
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data["all_data"]
    assert "products" in data["all_data"]
    cat_ids = {r["id"] for r in data["all_data"]["categories"]}
    for row in data["all_data"]["products"]:
        assert row["category_id"] in cat_ids, "FK constraint violated"

