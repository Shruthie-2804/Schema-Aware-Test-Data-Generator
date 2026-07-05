# Architecture — AI-Powered Schema-Aware Test Data Generator

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/Vite)                    │
│  Upload → AI Recommend → AI Preview → Generator → Data → Export │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (FastAPI)
┌──────────────────────────▼──────────────────────────────────────┐
│                     BACKEND (FastAPI / Python)                   │
│                                                                  │
│   api.py                                                         │
│   ├── /api/parse              → ddl_parser.py                    │
│   ├── /api/generate           → data_generator.py (Faker)       │
│   ├── /api/generate/hybrid    → hybrid_generator.py             │
│   ├── /api/ai/classify-schema → schema_classifier.py            │
│   ├── /api/ai/regenerate-schema → schema_regenerator.py         │
│   ├── /api/ai/explain-*       → agent.py                         │
│   └── /api/download/*         → exporters.py                    │
│                                                                  │
│   AI Layer (ai_provider.py)                                      │
│   ├── GeminiProvider     → Google Gemini REST API                │
│   ├── OpenAICompatible   → OpenAI / Groq / Together              │
│   └── FallbackProvider   → Faker-only mode (no API key)          │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Input (SQL DDL / JSON / CSV / Manual)
  │
  ▼
ddl_parser.py
  • Regex-based SQL parser
  • Extracts: tables, columns, types, PK, FK, UNIQUE, NOT NULL, DEFAULT
  │
  ▼
schema_classifier.py (no AI call — pure keyword matching)
  • Complexity: basic | medium | high | domain_specific
  • Domain: hospital | ecommerce | banking | education | ...
  • Recommendation: faker_only | hybrid | ai_regeneration
  │
  ▼  [if user selects AI regeneration]
schema_regenerator.py
  • Builds domain-specific prompt
  • Calls AI provider (Gemini / Groq / OpenAI)
  • Validates generated DDL using ddl_parser
  • Self-repairs invalid DDL (1 retry)
  • Returns SQL + explanation + table list
  │
  ▼
dependency_resolver.py
  • Topological sort of FK graph
  • Ensures parent tables are generated before child tables
  │
  ▼
hybrid_generator.py
  • For each column:
      if column is AI-eligible (semantic, TEXT type, not PK/FK):
        → pull from AI-generated value pool (cached)
      else:
        → generate with Faker
  • Maintains PK counter, FK lookup, UNIQUE sets
  │
  ▼
validators.py
  • PK uniqueness
  • FK consistency
  • NOT NULL compliance
  • Row count verification
  │
  ▼
exporters.py
  • CSV (one per table, pandas)
  • SQL INSERT statements
  • Markdown generation report
  │
  ▼
Download: SQL | CSV ZIP | JSON | MD Report | AI Report
```

## Module Responsibilities

| Module | Responsibility |
|---|---|
| `api.py` | FastAPI routes, request/response models |
| `ddl_parser.py` | SQL DDL → SchemaModel (no external lib) |
| `schema_models.py` | Dataclasses: SchemaModel, TableModel, ColumnModel, ForeignKeyModel |
| `schema_classifier.py` | Keyword-based complexity + domain detection |
| `schema_regenerator.py` | AI-powered full schema generation |
| `ai_provider.py` | Provider abstraction (Gemini, Groq, OpenAI, Fallback) |
| `hybrid_generator.py` | Routing columns to Faker vs AI, value caching |
| `dependency_resolver.py` | Topological sort for FK-safe generation order |
| `data_generator.py` | Pure Faker generation (original, preserved) |
| `agent.py` | Agent loop (OBSERVE→THINK→PLAN→ACT→VALIDATE→REPORT) |
| `validators.py` | Constraint checking |
| `exporters.py` | CSV, SQL, Markdown output |
| `utils.py` | Shared utilities |
