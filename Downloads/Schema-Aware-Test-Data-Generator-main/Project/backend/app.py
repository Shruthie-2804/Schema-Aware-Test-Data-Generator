"""
app.py
------
Streamlit web application for the Schema-Aware Test Data Generator.

Layout:
  - Sidebar: project info and configuration
  - Main panel: DDL input → Parse → Generate → Download

Usage:
  streamlit run app.py
"""

import os
import sys
import traceback

# Fix Windows charmap encoding issues — force UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import streamlit as st
import pandas as pd

# Ensure src/ is importable when running from project root
sys.path.insert(0, os.path.dirname(__file__))

from src.ddl_parser import parse_ddl, summarise_schema
from src.dependency_resolver import resolve_generation_order, describe_dependencies
from src.agent import DataGeneratorAgent
from src.data_generator import generate_all_data
from src.validators import run_all_validations
from src.exporters import (
    get_csv_zip_bytes,
    get_sql_bytes,
    get_report_bytes,
    export_csv_files,
    export_sql_inserts,
    export_report,
)
from src.utils import rows_to_dataframe, format_generation_order, get_schema_stats

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Schema-Aware Test Data Generator",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hero gradient header */
    .hero-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 8px 32px rgba(102,126,234,0.3);
    }
    .hero-header h1 { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .hero-header p  { font-size: 1rem; opacity: 0.9; margin-top: 0.5rem; }

    /* Metric card */
    .metric-card {
        background: white;
        border: 1px solid #e8ecf0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .metric-card .metric-value { font-size: 2rem; font-weight: 700; color: #667eea; }
    .metric-card .metric-label { font-size: 0.85rem; color: #6b7280; margin-top: 0.2rem; }

    /* Step badge */
    .step-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-radius: 50%;
        width: 28px; height: 28px;
        line-height: 28px;
        text-align: center;
        font-weight: 700;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }

    /* Table styles */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Success / error boxes */
    .success-box {
        background: #d1fae5; border: 1px solid #6ee7b7;
        border-radius: 10px; padding: 1rem; color: #065f46;
    }
    .error-box {
        background: #fee2e2; border: 1px solid #fca5a5;
        border-radius: 10px; padding: 1rem; color: #991b1b;
    }

    /* Agent log */
    .agent-log {
        background: #0f172a; color: #a3e635;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem; padding: 1.2rem;
        border-radius: 10px; max-height: 400px;
        overflow-y: auto; white-space: pre-wrap;
    }

    /* Download button strip */
    .download-strip {
        background: #f8faff;
        border: 1px solid #e0e7ff;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-top: 1rem;
    }

    /* Section title */
    .section-title {
        font-size: 1.15rem; font-weight: 600;
        color: #374151; margin-bottom: 0.8rem;
        border-bottom: 2px solid #e0e7ff;
        padding-bottom: 0.4rem;
    }

    /* Sidebar style */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
    }
    [data-testid="stSidebar"] * { color: #e0e7ff !important; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: white !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Default Sample Schema (e-commerce)
# ---------------------------------------------------------------------------
ECOMMERCE_SAMPLE = """-- E-Commerce Sample Schema
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

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧪 Test Data Generator")
    st.markdown("**Infinite Computer Solutions**")
    st.markdown("*Tech Round AI Prototype Challenge*")
    st.divider()

    st.markdown("### ⚙️ Configuration")
    num_rows = st.number_input(
        "Rows per table",
        min_value=1, max_value=500, value=10, step=1,
        help="How many rows to generate for each table.",
    )
    st.divider()

    st.markdown("### 🤖 Agent Loop Steps")
    for step in ["OBSERVE", "THINK", "PLAN", "ACT", "VALIDATE", "REPORT"]:
        st.markdown(f"✅ **{step}**")
    st.divider()

    st.markdown("### 📚 Quick Links")
    st.markdown("- [README](README.md)")
    st.markdown("- [Architecture](docs/architecture.md)")

# ---------------------------------------------------------------------------
# Hero Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-header">
  <h1>🧪 Schema-Aware Test Data Generator</h1>
  <p>
    AI-powered realistic test data generation that understands your database schema,
    respects foreign key relationships, and exports SQL INSERTs + CSV files instantly.
  </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Problem Statement
# ---------------------------------------------------------------------------
with st.expander("📌 Problem Statement", expanded=False):
    st.markdown("""
    **Business Problem:** Test environments need realistic test data tied to database foreign key relationships.
    Developers and testers often manually create sample rows — a tedious process when tables have primary keys,
    foreign keys, unique constraints, nullable fields, and parent-child relationships.

    **Solution:** This tool reads SQL DDL, understands schema structure, and auto-generates
    referentially consistent, realistic test data using an **AI-style agent loop** + **Faker**.
    """)

st.divider()

# ---------------------------------------------------------------------------
# Step 1: DDL Input
# ---------------------------------------------------------------------------
st.markdown('<div class="section-title"><span class="step-badge">1</span> Provide SQL DDL Schema</div>',
            unsafe_allow_html=True)

input_col1, input_col2 = st.columns([3, 1])

with input_col1:
    ddl_input = st.text_area(
        "Paste your SQL DDL here",
        value=ECOMMERCE_SAMPLE,
        height=280,
        placeholder="CREATE TABLE users (...);",
        label_visibility="collapsed",
    )

with input_col2:
    st.markdown("#### 📁 Upload .sql File")
    uploaded_file = st.file_uploader(
        "Or upload a .sql file",
        type=["sql"],
        label_visibility="collapsed",
    )
    if uploaded_file:
        ddl_input = uploaded_file.read().decode("utf-8")
        st.success(f"✅ Loaded: `{uploaded_file.name}`")

    st.markdown("#### 🎯 Sample Schemas")
    sample_choice = st.selectbox(
        "Load a sample",
        ["E-Commerce", "College / University"],
        label_visibility="collapsed",
    )
    if st.button("📂 Load Sample", use_container_width=True):
        if sample_choice == "College / University":
            try:
                from src.utils import load_ddl_from_file
                ddl_input = load_ddl_from_file(
                    "sample_data/input_schemas/college_schema.sql"
                )
            except Exception:
                ddl_input = ECOMMERCE_SAMPLE
        else:
            ddl_input = ECOMMERCE_SAMPLE
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Step 2: Parse + Generate
# ---------------------------------------------------------------------------
st.markdown('<div class="section-title"><span class="step-badge">2</span> Parse & Generate</div>',
            unsafe_allow_html=True)

generate_btn = st.button(
    "🚀 Generate Test Data",
    type="primary",
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------
if generate_btn and ddl_input.strip():
    progress_bar = st.progress(0, text="Starting agent loop…")

    try:
        # ---- PARSE --------------------------------------------------------
        progress_bar.progress(10, text="🔍 Parsing DDL schema…")
        schema = parse_ddl(ddl_input)
        st.success(f"✅ Parsed **{len(schema.tables)}** table(s) successfully.")

        # ---- DEPENDENCY RESOLUTION ----------------------------------------
        progress_bar.progress(25, text="🔗 Resolving FK dependencies…")
        generation_order = resolve_generation_order(schema)

        # ---- AGENT LOOP ---------------------------------------------------
        progress_bar.progress(35, text="🤖 Agent OBSERVE + THINK…")
        agent = DataGeneratorAgent(schema, num_rows)
        agent.observe()
        agent.think()
        agent.plan(generation_order)

        # ---- GENERATE -----------------------------------------------------
        progress_bar.progress(55, text="⚙️ Agent ACT — generating data…")
        all_data = generate_all_data(schema, generation_order, num_rows, agent)

        # ---- VALIDATE -----------------------------------------------------
        progress_bar.progress(75, text="✅ Agent VALIDATE — checking integrity…")
        agent.validate_start()
        passed, issues = run_all_validations(schema, all_data, num_rows)
        agent.validate_result(passed, issues)

        # ---- REPORT -------------------------------------------------------
        progress_bar.progress(90, text="📊 Agent REPORT — preparing outputs…")
        agent.report(all_data)

        # ---- SAVE OUTPUTS -------------------------------------------------
        out_dir = "sample_data/outputs"
        os.makedirs(out_dir, exist_ok=True)
        os.makedirs(os.path.join(out_dir, "csv"), exist_ok=True)

        export_csv_files(all_data, out_dir)
        sql_path = os.path.join(out_dir, "generated_inserts.sql")
        export_sql_inserts(schema, all_data, generation_order, sql_path)
        rpt_path = os.path.join(out_dir, "generation_report.md")
        export_report(
            schema, all_data, generation_order,
            passed, issues, agent.get_full_log(), rpt_path
        )

        progress_bar.progress(100, text="🎉 Complete!")

        # ---- Store in session state ----------------------------------------
        st.session_state["schema"]           = schema
        st.session_state["all_data"]         = all_data
        st.session_state["generation_order"] = generation_order
        st.session_state["agent"]            = agent
        st.session_state["passed"]           = passed
        st.session_state["issues"]           = issues
        st.session_state["generated"]        = True

    except ValueError as e:
        progress_bar.empty()
        st.markdown(f'<div class="error-box">❌ <strong>Parse Error:</strong> {e}</div>',
                    unsafe_allow_html=True)
    except Exception as e:
        progress_bar.empty()
        st.markdown(f'<div class="error-box">❌ <strong>Unexpected Error:</strong> {e}</div>',
                    unsafe_allow_html=True)
        with st.expander("🐛 Traceback"):
            st.code(traceback.format_exc())

elif generate_btn:
    st.warning("⚠️ Please provide DDL SQL before generating.")

# ---------------------------------------------------------------------------
# Results Section
# ---------------------------------------------------------------------------
if st.session_state.get("generated"):
    schema           = st.session_state["schema"]
    all_data         = st.session_state["all_data"]
    generation_order = st.session_state["generation_order"]
    agent            = st.session_state["agent"]
    passed           = st.session_state["passed"]
    issues           = st.session_state["issues"]

    st.divider()

    # ---- Metrics Row -------------------------------------------------------
    from src.utils import get_schema_stats
    stats = get_schema_stats(schema, all_data)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{stats['tables']}</div>
          <div class="metric-label">Tables Detected</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{stats['total_columns']}</div>
          <div class="metric-label">Total Columns</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{stats['total_rows_generated']}</div>
          <div class="metric-label">Rows Generated</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{stats['fk_relationships']}</div>
          <div class="metric-label">FK Relationships</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ---- Tabs --------------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Schema Summary",
        "🔗 Generation Order",
        "📊 Generated Data",
        "🤖 Agent Log",
        "⬇️ Downloads",
    ])

    # TAB 1 — Schema Summary
    with tab1:
        st.markdown("### Parsed Schema")
        st.code(summarise_schema(schema), language="text")
        st.markdown("### FK Dependency Graph")
        st.code(describe_dependencies(schema), language="text")

        st.markdown("### Column Detail")
        for tname, table in schema.tables.items():
            with st.expander(f"📌 `{tname}` — {len(table.columns)} columns"):
                col_data = []
                for col in table.columns:
                    col_data.append({
                        "Column": col.name,
                        "Type": col.data_type,
                        "PK": "✅" if col.is_primary_key else "",
                        "Nullable": "✅" if col.is_nullable else "❌",
                        "Unique": "✅" if col.is_unique else "",
                        "Default": col.default_value or "",
                        "Max Len": col.max_length or "",
                    })
                st.dataframe(pd.DataFrame(col_data), use_container_width=True)

    # TAB 2 — Generation Order
    with tab2:
        st.markdown("### Table Generation Order")
        st.markdown(
            "> Parent tables are always generated **before** their child tables "
            "to ensure foreign key consistency."
        )
        st.markdown(
            f"**Order:** `{format_generation_order(generation_order)}`"
        )

        # Visual flow
        cols = st.columns(len(generation_order))
        for i, (col, tname) in enumerate(zip(cols, generation_order)):
            with col:
                tbl = schema.get_table(tname)
                fk_count = len(tbl.foreign_keys) if tbl else 0
                icon = "🌱" if fk_count == 0 else "🌿"
                st.markdown(f"""
                <div style="background:#f0f4ff;border:1px solid #c7d2fe;
                     border-radius:10px;padding:0.8rem;text-align:center;">
                  <div style="font-size:1.5rem">{icon}</div>
                  <div style="font-weight:600;color:#4338ca">{tname}</div>
                  <div style="font-size:0.75rem;color:#6b7280">
                    {'Root table' if fk_count == 0 else f'{fk_count} FK(s)'}
                  </div>
                  <div style="font-size:0.7rem;color:#9ca3af;margin-top:0.2rem">
                    Step {i+1}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            if i < len(generation_order) - 1:
                pass  # Arrow is implicit from left-to-right layout

    # TAB 3 — Generated Data
    with tab3:
        st.markdown("### Generated Data Preview")
        for tname in generation_order:
            rows = all_data.get(tname, [])
            if not rows:
                continue
            with st.expander(f"📊 `{tname}` — {len(rows)} rows", expanded=True):
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)

    # TAB 4 — Agent Log
    with tab4:
        st.markdown("### 🤖 Agent Reasoning Loop")
        st.markdown("""
        The agent processes your schema through 6 steps:
        **OBSERVE → THINK → PLAN → ACT → VALIDATE → REPORT**
        """)
        log_text = agent.get_full_log()
        st.markdown(f'<div class="agent-log">{log_text}</div>', unsafe_allow_html=True)

        # Validation result
        st.markdown("### Validation Result")
        if passed:
            st.markdown('<div class="success-box">✅ <strong>All checks passed!</strong> '
                        'Referential integrity is maintained.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="error-box">⚠️ <strong>{len(issues)} issue(s) found:</strong>'
                        '<br>' + '<br>'.join(f"• {i}" for i in issues) + '</div>',
                        unsafe_allow_html=True)

    # TAB 5 — Downloads
    with tab5:
        st.markdown("### ⬇️ Download Generated Outputs")
        st.markdown('<div class="download-strip">', unsafe_allow_html=True)

        dl1, dl2, dl3 = st.columns(3)

        with dl1:
            st.markdown("#### 🗄️ SQL INSERT File")
            sql_bytes = get_sql_bytes(schema, all_data, generation_order)
            st.download_button(
                label="⬇️ Download SQL INSERTs",
                data=sql_bytes,
                file_name="generated_inserts.sql",
                mime="text/sql",
                use_container_width=True,
            )
            st.caption("Contains INSERT statements for all tables in correct FK order.")

        with dl2:
            st.markdown("#### 📁 CSV Files (ZIP)")
            zip_bytes = get_csv_zip_bytes(all_data)
            st.download_button(
                label="⬇️ Download All CSVs (ZIP)",
                data=zip_bytes,
                file_name="generated_csv_files.zip",
                mime="application/zip",
                use_container_width=True,
            )
            st.caption(f"Contains {len(all_data)} CSV file(s), one per table.")

        with dl3:
            st.markdown("#### 📝 Generation Report")
            rpt_bytes = get_report_bytes(
                schema, all_data, generation_order,
                passed, issues, agent.get_full_log()
            )
            st.download_button(
                label="⬇️ Download Report (Markdown)",
                data=rpt_bytes,
                file_name="generation_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.caption("Includes schema summary, validation result, and agent log.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Individual CSVs
        st.markdown("#### Individual CSV Downloads")
        from src.exporters import get_csv_bytes
        csv_bytes_map = get_csv_bytes(all_data)
        cols = st.columns(min(len(csv_bytes_map), 4))
        for i, (tname, csv_bytes) in enumerate(csv_bytes_map.items()):
            with cols[i % len(cols)]:
                st.download_button(
                    label=f"⬇️ {tname}.csv",
                    data=csv_bytes,
                    file_name=f"{tname}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.markdown("""
<div style="text-align:center; color:#9ca3af; font-size:0.85rem; padding:1rem 0;">
  🧪 <strong>Schema-Aware Test Data Generator</strong> &nbsp;|&nbsp;
  Built for <strong>Infinite Computer Solutions Tech Round AI Prototype Challenge</strong><br>
  Agent Loop • Faker • Python • Streamlit &nbsp;|&nbsp;
  Open Source • Free to Use
</div>
""", unsafe_allow_html=True)
