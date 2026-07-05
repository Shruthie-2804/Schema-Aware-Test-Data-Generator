# Schema-Aware Test Data Generator — Complete Team Explanation

> **For:** Infinite Computer Solutions Tech Round AI Prototype Challenge  
> **Read this if:** You want to understand the ENTIRE project from scratch, including the modern full-stack architecture and AI integrations.

---

## PART 1 — THE PROBLEM STATEMENT

### What is a Database Schema?

A database schema is a blueprint of your database. It defines what tables exist, what columns each table has, and how tables are connected to each other.

Example schema for an online shopping app:

```sql
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
```

The `FOREIGN KEY` line means: every `user_id` value in `orders` MUST exist as an `id` in the `users` table. This is called **Referential Integrity**.

---

### What is Test Data and Why Do We Need It?

When developers build an app, they need fake/sample rows in the database to:
- Test if their API returns the right data
- Test if the UI displays correctly
- Test edge cases (NULL values, long strings, zero quantities)
- Demo the product to a client or stakeholder

---

### The Actual Problem

Imagine your database has 6 tables with 40+ columns and 5 foreign key relationships:

```
users ──────────────────────► orders ──────► order_items
                                                   ▲
products ──────────────────────────────────────────┘
departments ────► employees ──► payroll
```

To insert test data manually:
1. You must insert `users` BEFORE `orders` (FK rule)
2. You must insert `products` BEFORE `order_items` (FK rule)
3. Every `user_id` in `orders` must be a real user ID
4. Every `product_id` in `order_items` must be a real product ID
5. You must repeat this for ALL tables in the CORRECT order

**This is painful, slow, and error-prone.** If you get the order wrong or use a wrong ID, the database throws a Foreign Key Violation error and rejects your data.

---

### The Business Impact

| Problem | Impact |
|---------|--------|
| Manual data creation | 2–4 hours wasted per developer per sprint |
| Wrong FK values | Tests fail, debugging wastes time |
| Inconsistent test data | Bugs hide in production |
| No realistic data | Demos look unprofessional |

---

## PART 2 — OUR SOLUTION

We built a full-stack, enterprise-ready application that:

1. **Reads** your SQL `CREATE TABLE` DDL statements.
2. **Understands** the structure — columns, types, primary keys, foreign keys, constraints.
3. **Figures out** the correct generation order (parents before children) using a graph dependency resolver.
4. **Leverages AI-Powered Recommendations** to classify column data types and suggest AI generation for domain-specific fields.
5. **Generates** realistic fake data using a **Hybrid Engine**:
   - Standard columns (names, emails, dates) are populated locally and instantly via the **Faker** library.
   - Domain-specific text columns (medical diagnoses, product reviews, descriptions) are generated using state-of-the-art LLMs (Gemini / Groq / OpenAI).
6. **Enforces & Validates** referential integrity (checking primary keys, foreign keys, and NOT NULL constraints).
7. **Exports** SQL INSERT statements, ZIP archives of CSV files, and detailed generation reports.

**Time to generate 50 rows across 5 tables: Under 2 seconds.**

---

## PART 3 — TECH STACK AND WHY WE CHOSE EACH

We migrated from a simple single-page prototype to a professional full-stack architecture:

| Technology | What It Is | Why We Used It |
|-----------|-----------|----------------|
| **Python 3.10+** | Programming language | Industry standard for data tools, rich ecosystem. |
| **FastAPI** | Backend Web API | Lightning-fast, async support, auto-generated OpenAPI (Swagger) documentation, and type safety. |
| **React + Vite** | Frontend Framework | High-performance, components-based UI with fast development reloads. |
| **Zustand** | State Management | Simple, lightweight, and robust state container to share DDL schemas and generated data across different wizard steps. |
| **Faker** | Python library | Generates realistic local data (names, emails, phones, addresses). |
| **pandas** | Data manipulation | Formats rows into clean CSV structures for exports. |
| **pytest** | Testing framework | Performs automated, mocked tests on backend logic. |
| **Custom Topological Sort** | Algorithm | Implemented Kahn's algorithm to resolve table dependency ordering without bloated external libraries. |

### Why React + FastAPI instead of a single-file script?
- **Real-World Experience:** Demonstrates production-grade separation of concerns.
- **Better UX:** Step-by-step wizard guides the user from raw schema input, through AI analysis, to previewing and exporting.
- **Asynchronous Execution:** Heavy AI generation jobs run asynchronously, preventing browser tabs from freezing.

---

## PART 4 — DO WE USE ANY LLM OR API KEY?

### Yes, and it is a key differentiator.

To make this a true AI prototype, we integrated actual LLMs while keeping costs at zero.

1. **AI Schema Classifier (`schema_classifier.py`):**
   - Automatically inspects the uploaded schema.
   - Checks columns for domain keywords (like *diagnosis*, *treatment*, *review*, *comment*, *description*).
   - Recommends whether to run in pure Faker mode, Hybrid mode, or full AI schema regeneration.

2. **AI Schema Regenerator (`schema_regenerator.py`):**
   - If a user uploads an incomplete schema (e.g., just `users` and `orders`), they can ask the AI to expand it.
   - The LLM writes a complete, professionally designed relational database schema (e.g., E-Commerce or Healthcare) in clean SQL DDL.
   - The backend validates the generated DDL. If there's an error, it performs a self-repair attempt.

3. **AI Hybrid Generation (`hybrid_generator.py`):**
   - For domain-specific columns, calling the AI for every single row is slow and expensive.
   - **Our Innovation (Smart Value Pooling):** We call the LLM once per table to generate a pool of 20 unique, realistic values (e.g., 20 unique patient diagnoses).
   - We cache this pool and randomly select from it during generation. This reduces API calls by **95%**, keeps generation times under 2 seconds, and respects free-tier rate limits!

---

## PART 5 — THE AGENT LOOP

Our generator uses the **Agent Loop** design pattern (`src/agent.py` or equivalent tracing logic) to observe, plan, and self-validate:

```
[OBSERVE]  →  Analyze the input DDL schema and detect tables/columns.
[THINK]    →  Classify column types (Faker rule vs AI domain field).
[PLAN]     →  Sort tables topologically to determine correct insert order.
[ACT]      →  Generate rows using Faker + cached LLM value pools.
[VALIDATE] →  Run integrity checks (verify parent IDs exist before child IDs).
[REPORT]   →  Output clean SQL, ZIP archives of CSVs, and an execution summary.
```

---

## PART 6 — DATA FLOW

```
User uploads SQL Schema
           │
           ▼
     [ddl_parser.py] ───► Extract tables, columns, primary/foreign keys
           │
           ▼
   [schema_classifier.py] ───► Analyze complexity & domain
           │
           ├─────────────────────────┐
           ▼ (AI Regeneration)        ▼ (Faker/Hybrid Setup)
   [schema_regenerator.py]     [dependency_resolver.py] (Topological Sort)
           │                                 │
           └───────────────►                 ▼
                                    [hybrid_generator.py]
                                 • Standard fields → Faker
                                 • Complex fields → Cached LLM Pool
                                             │
                                             ▼
                                      [validators.py]
                                 • Check PK uniqueness
                                 • Check FK references exist
                                             │
                                             ▼
                                       [exporters.py]
                                 • Generate SQL Inserts
                                 • Create ZIP of CSVs
```

---

## PART 7 — FILE STRUCTURE EXPLAINED

```
schema-aware-test-data-generator/
├── README.md                      ← General user guide (what we show on GitHub)
├── .gitignore                     ← Rules to keep keys and dependencies out of Git
│
├── Document/                      ← Supporting documentations
│   ├── AI_USAGE_NOTE.md           ← Transparency on how AI was implemented
│   ├── TEAM_EXPLANATION.md        ← THIS FILE
│   ├── architecture.md            ← Architecture diagram
│   ├── assumptions_limitations.md ← Scope limits (e.g., circular dependencies)
│   └── prompts_used.md            ← Prompt engineering logs
│
├── Project/
│   ├── backend/                   ← FastAPI service
│   │   ├── api.py                 ← Main API endpoints
│   │   ├── requirements.txt       ← Python dependencies
│   │   ├── .env.example           ← Environment variables template
│   │   ├── src/                   ← Core Python modules
│   │   │   ├── ai_provider.py     ← API wrapper for Gemini, Groq, and OpenAI
│   │   │   ├── hybrid_generator.py ← Faker + LLM generation router
│   │   │   ├── schema_classifier.py ← Analyzes schemas & suggests generators
│   │   │   └── schema_regenerator.py ← LLM-powered DDL schema builder
│   │   └── tests/                 ← Test suite (pytest)
│   │
│   └── frontend/                  ← React user interface
│       ├── package.json           ← Dependencies & scripts
│       ├── vite.config.ts         ← Vite bundler settings
│       ├── src/                   ← React components & TanStack routes
```

---

## PART 8 — TEST SUITE

Run the tests inside `Project/backend` using:
```bash
pytest
```
*Note: All AI API calls in the test suite are mocked, meaning tests can run offline and without API keys!*

---

## PART 9 — COLLABORATIVE TEAM CONTRIBUTIONS

To demonstrate teamwork for the placement round, responsibilities were divided cleanly:

1.  **🔴 Core Engine & Backend API (Priority 1 - Lead):**
    *   Designed the FastAPI server, DDL parser, Kahn's topological sorter, and the hybrid Faker-LLM generation logic.
2.  **🟡 Frontend User Interface (Priority 2 - Secondary):**
    *   Built the multi-step React web app, styling transitions, and Zustund state syncing.
3.  **🟢 QA & Testing (Priority 3 - Secondary):**
    *   Wrote the mock testing suite validating the parser, dependency resolver, generator, and validators.
4.  **🔵 Documentation & Video (Priority 4 - Support):**
    *   Documented system architecture, usage limitations, prompt engineering logs, and recorded the demo presentation.

---

## PART 10 — SUMMARY FOR INTERVIEWERS

> "We built a full-stack, AI-powered Schema-Aware Test Data Generator using React and FastAPI. The system reads SQL schema statements, resolves foreign key dependencies using Kahn's topological sort, and generates referentially consistent synthetic data. 
> 
> To generate high-quality text columns (like medical descriptions) without hitting rate limits or incurring costs, we implemented a Hybrid Engine. It routes standard fields to the Faker library and uses a cached value pool generated from LLM APIs (Gemini/Groq) for complex fields. The user can also upload basic schemas and have the LLM expand them into production-ready schemas. The entire backend is covered by automated unit tests."
