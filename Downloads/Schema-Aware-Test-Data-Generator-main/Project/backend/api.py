"""
api.py
------
FastAPI application for the AI-Powered Schema-Aware Test Data Generator.

Endpoints (existing — preserved):
  GET  /health
  POST /api/parse
  POST /api/ai/explain-schema
  POST /api/generate
  GET  /api/download/sql
  GET  /api/download/csv
  GET  /api/download/report

New AI endpoints:
  POST /api/ai/classify-schema       — schema complexity + domain detection
  POST /api/ai/regenerate-schema     — AI-powered schema regeneration
  POST /api/generate/hybrid          — Faker + AI hybrid data generation
  POST /api/ai/explain-generation    — explain what the system generated

Environment variables (from .env):
  AI_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY
"""

import os
import sys
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import shutil

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — env vars may be set by the OS

sys.path.insert(0, os.path.dirname(__file__))

from src.ddl_parser import parse_ddl, summarise_schema
from src.dependency_resolver import resolve_generation_order
from src.agent import DataGeneratorAgent
from src.data_generator import generate_all_data
from src.validators import run_all_validations
from src.exporters import export_csv_files, export_sql_inserts, export_report
from src.schema_classifier import classify_schema
from src.schema_regenerator import regenerate_schema
from src.hybrid_generator import generate_all_data_hybrid
from src.ai_provider import get_provider

app = FastAPI(
    title="AI-Powered Schema-Aware Test Data Generator API",
    version="2.0.0",
    description="Generates realistic test data using Faker + AI for any SQL schema.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# ===========================================================================
# Request / Response models
# ===========================================================================

class ParseRequest(BaseModel):
    ddl: str

class GenerateRequest(BaseModel):
    ddl: str
    num_rows: int
    preserve_integrity: bool = True

class ExplainRequest(BaseModel):
    ddl: str

class ClassifySchemaRequest(BaseModel):
    ddl_schema: str
    selected_domain: Optional[str] = None

class RegenerateSchemaRequest(BaseModel):
    original_schema: str
    input_type: str = "sql"
    domain: str
    user_instruction: str = ""
    confirm_regeneration: bool = True

class HybridGenerateRequest(BaseModel):
    ddl_schema: str
    rows_per_table: int = 10
    generation_mode: str = "auto"   # auto | faker_only | hybrid
    domain: str = "general"

class ExplainGenerationRequest(BaseModel):
    ddl_schema: str
    domain: str = "general"
    generation_mode_used: str = "faker_only"   # auto | faker_only | hybrid
    faker_generated_fields: List[str] = []
    ai_generated_fields: List[str] = []
    validation_passed: bool = True
    validation_issues: List[str] = []


# ===========================================================================
# Existing endpoints (preserved exactly)
# ===========================================================================

@app.get("/health")
def health_check():
    provider = get_provider()
    return {
        "status": "ok",
        "message": "Backend is running and connected.",
        "ai_provider": provider.provider_name,
        "ai_available": provider.is_available(),
    }


@app.post("/api/parse")
def parse_schema(req: ParseRequest):
    try:
        schema = parse_ddl(req.ddl)
        order = resolve_generation_order(schema)
        tables_info = []
        for tname, table in schema.tables.items():
            tables_info.append({
                "name": tname,
                "columns": [
                    {
                        "name": c.name,
                        "type": c.data_type,
                        "pk": c.is_primary_key,
                        "fk": next((fk.ref_table for fk in table.foreign_keys if fk.column == c.name), None),
                    }
                    for c in table.columns
                ],
                "foreign_keys": [fk.column for fk in table.foreign_keys],
            })
        return {
            "success": True,
            "tables": tables_info,
            "generation_order": order,
            "summary": summarise_schema(schema),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/ai/explain-schema")
def explain_schema(req: ExplainRequest):
    try:
        schema = parse_ddl(req.ddl)
        summary = summarise_schema(schema)
        agent = DataGeneratorAgent(schema, 10)
        explanation = (
            f"This schema contains {len(schema.tables)} tables. {summary}\n\n"
            "The system has detected the foreign key relationships and understands "
            "the optimal generation order."
        )
        return {"success": True, "explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate")
def generate_data(req: GenerateRequest):
    try:
        schema = parse_ddl(req.ddl)
        generation_order = resolve_generation_order(schema)

        agent = DataGeneratorAgent(schema, req.num_rows)
        agent.observe()
        agent.think()
        agent.plan(generation_order)

        all_data = generate_all_data(schema, generation_order, req.num_rows, agent)

        agent.validate_start()
        passed, issues = run_all_validations(schema, all_data, req.num_rows)
        agent.validate_result(passed, issues)
        agent.report(all_data)

        out_dir = os.path.join(ROOT_DIR, "sample_data", "output")
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(os.path.join(out_dir, "csv"), exist_ok=True)

        export_csv_files(all_data, out_dir)
        sql_path = os.path.join(out_dir, "generated_inserts.sql")
        export_sql_inserts(schema, all_data, generation_order, sql_path)
        rpt_path = os.path.join(out_dir, "generation_report.md")
        export_report(schema, all_data, generation_order, passed, issues, agent.get_full_log(), rpt_path)

        return {
            "success": True,
            "generation_order": generation_order,
            "all_data": all_data,
            "passed": passed,
            "issues": issues,
            "agent_log": agent.get_full_log(),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# NEW endpoint 1 — Classify schema
# ===========================================================================

@app.post("/api/ai/classify-schema")
def classify_schema_endpoint(req: ClassifySchemaRequest):
    """
    Analyse schema complexity, detect domain, and recommend generation mode.
    No AI API call required — pure keyword analysis.
    """
    try:
        schema = parse_ddl(req.ddl_schema)
        result = classify_schema(schema, selected_domain=req.selected_domain)
        return {
            "success": True,
            "complexity": result.complexity,
            "detected_domain": result.detected_domain,
            "selected_domain": req.selected_domain or "none",
            "recommendation": result.recommendation,
            "reason": result.reason,
            "ai_columns": result.ai_columns,
            "faker_columns": result.faker_columns[:10],  # preview first 10
            "domain_scores": result.domain_score,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================================================
# NEW endpoint 2 — Regenerate schema using AI
# ===========================================================================

@app.post("/api/ai/regenerate-schema")
def regenerate_schema_endpoint(req: RegenerateSchemaRequest):
    """
    Use AI to generate or improve a schema for the given domain.
    Returns the AI-generated SQL DDL, explanation, and table list.
    The caller must confirm before applying (confirm_regeneration flag is informational).
    """
    try:
        provider = get_provider()
        result = regenerate_schema(
            original_ddl=req.original_schema,
            domain=req.domain,
            user_instruction=req.user_instruction,
            provider=provider,
        )
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# NEW endpoint 3 — Hybrid data generation
# ===========================================================================

@app.post("/api/generate/hybrid")
def generate_hybrid(req: HybridGenerateRequest):
    """
    Generate test data using Faker for basic fields and AI for semantic fields.
    Respects PK, FK, UNIQUE, NOT NULL constraints.
    """
    try:
        schema = parse_ddl(req.ddl_schema)
        generation_order = resolve_generation_order(schema)

        # Agent loop
        agent = DataGeneratorAgent(schema, req.rows_per_table)
        agent.observe()
        agent.think()
        agent.plan(generation_order)

        # Decide mode
        provider = get_provider()
        force_faker = (req.generation_mode == "faker_only") or not provider.is_available()

        if force_faker or req.generation_mode == "faker_only":
            all_data = generate_all_data(schema, generation_order, req.rows_per_table, agent)
            agent.validate_start()
            passed, issues = run_all_validations(schema, all_data, req.rows_per_table)
            agent.validate_result(passed, issues)
            agent.report(all_data)

            # Collect faker fields
            faker_fields = []
            for tname, table in schema.tables.items():
                for col in table.columns:
                    if not col.is_primary_key:
                        faker_fields.append(f"{tname}.{col.name}")

            result = {
                "success": True,
                "generation_mode_used": "faker_only",
                "faker_generated_fields": faker_fields,
                "ai_generated_fields": [],
                "data": all_data,
                "provider_used": "faker",
                "validation": {"passed": passed, "issues": issues},
                "agent_log": agent.get_full_log(),
            }
        else:
            hybrid_result = generate_all_data_hybrid(
                schema=schema,
                generation_order=generation_order,
                num_rows=req.rows_per_table,
                domain=req.domain,
                provider=provider,
                agent=agent,
            )
            all_data = hybrid_result["data"]
            agent.validate_start()
            passed, issues = run_all_validations(schema, all_data, req.rows_per_table)
            agent.validate_result(passed, issues)
            agent.report(all_data)

            result = {
                "success": True,
                "generation_mode_used": hybrid_result["generation_mode_used"],
                "faker_generated_fields": hybrid_result["faker_generated_fields"],
                "ai_generated_fields": hybrid_result["ai_generated_fields"],
                "data": all_data,
                "provider_used": hybrid_result["provider_used"],
                "validation": {"passed": passed, "issues": issues},
                "agent_log": agent.get_full_log(),
            }

        # Export to disk
        out_dir = os.path.join(ROOT_DIR, "sample_data", "output")
        os.makedirs(out_dir, exist_ok=True)
        export_csv_files(all_data, out_dir)
        sql_path = os.path.join(out_dir, "generated_inserts.sql")
        export_sql_inserts(schema, all_data, generation_order, sql_path)
        rpt_path = os.path.join(out_dir, "generation_report.md")
        export_report(
            schema, all_data, generation_order,
            result["validation"]["passed"], result["validation"]["issues"],
            agent.get_full_log(), rpt_path,
        )

        result["downloads"] = {
            "sql": "/api/download/sql",
            "csv": "/api/download/csv",
            "report": "/api/download/report",
        }
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ===========================================================================
# NEW endpoint 4 — Explain generation
# ===========================================================================

@app.post("/api/ai/explain-generation")
def explain_generation(req: ExplainGenerationRequest):
    """
    Return a structured explanation of how the data was generated.
    """
    try:
        schema = parse_ddl(req.ddl_schema)
        table_names = list(schema.tables.keys())
        total_cols = sum(len(t.columns) for t in schema.tables.values())

        return {
            "success": True,
            "input_type": "sql_ddl",
            "domain": req.domain,
            "generation_mode_used": req.generation_mode_used,
            "tables_generated": table_names,
            "total_columns": total_cols,
            "faker_generated_fields": req.faker_generated_fields,
            "ai_generated_fields": req.ai_generated_fields,
            "ai_columns_count": len(req.ai_generated_fields),
            "faker_columns_count": len(req.faker_generated_fields),
            "validation_result": {
                "passed": req.validation_passed,
                "issues": req.validation_issues,
                "issues_count": len(req.validation_issues),
            },
            "explanation": (
                f"Generated data for {len(table_names)} table(s) using "
                f"'{req.generation_mode_used}' mode. "
                f"{len(req.faker_generated_fields)} field(s) were generated by Faker, "
                f"{len(req.ai_generated_fields)} field(s) by AI. "
                f"Validation {'passed' if req.validation_passed else 'found ' + str(len(req.validation_issues)) + ' issue(s)'}."
            ),
            "ai_provider_note": (
                "AI was used for domain-specific semantic fields."
                if req.ai_generated_fields
                else "Faker-only mode was used. No AI API calls were made."
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===========================================================================
# Download endpoints (existing — preserved)
# ===========================================================================

@app.get("/api/download/sql")
def download_sql():
    path = os.path.join(ROOT_DIR, "sample_data", "output", "generated_inserts.sql")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="SQL file not found. Generate data first.")
    return FileResponse(path, filename="generated_inserts.sql", media_type="application/sql")


@app.get("/api/download/csv")
def download_csv():
    csv_dir = os.path.join(ROOT_DIR, "sample_data", "output", "csv")
    if not os.path.exists(csv_dir):
        raise HTTPException(status_code=404, detail="CSV directory not found. Generate data first.")
    zip_path = os.path.join(ROOT_DIR, "sample_data", "output", "generated_csvs.zip")
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", csv_dir)
    return FileResponse(zip_path, filename="generated_csvs.zip", media_type="application/zip")


@app.get("/api/download/report")
def download_report():
    path = os.path.join(ROOT_DIR, "sample_data", "output", "generation_report.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report file not found. Generate data first.")
    return FileResponse(path, filename="generation_report.md", media_type="text/markdown")


# ===========================================================================
# AI status endpoint — quick health check for the frontend
# ===========================================================================

@app.get("/api/ai/status")
def ai_status():
    """Return current AI provider status."""
    provider = get_provider()
    return {
        "provider": provider.provider_name,
        "available": provider.is_available(),
        "mode": "ai" if provider.is_available() else "faker_only",
        "note": (
            "AI provider is ready."
            if provider.is_available()
            else "No AI provider configured. Using Faker-only mode. "
                 "Set AI_PROVIDER and API key in .env to enable AI features."
        ),
    }
