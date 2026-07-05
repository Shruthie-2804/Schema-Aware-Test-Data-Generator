# AI-Powered Schema-Aware Test Data Generator

> **Version 2.0 — Full-Stack AI-Powered Synthetic Data Platform**  
> Developed for the Placement Technical Round Prototype at Infinite Computer Solutions

---

## 🌟 What is this Project? (For Everyone)

Imagine you are building a new application (like a hospital booking system or an online shop). Before launching, you need to test it with a lot of data. 

But there are two main problems:
1. **Security & Privacy:** You cannot use real customer or patient data due to privacy laws.
2. **Realistic Quality:** If you use simple dummy text (like "test1", "abcde"), it looks fake, makes it hard to test search features, and doesn't represent real-world scenarios.

**The Solution:** This project is a **Smart Test Data Generator**. It reads your database structure (the blueprint) and automatically generates realistic, secure, and fully connected mock data.

### 🔮 The Hybrid Magic (How it Works)
To keep the application lightning-fast and cost-effective, the system uses two engines:
*   **The Rule-Based Engine (Faker):** For standard fields like names, phone numbers, emails, addresses, and dates. This is extremely fast and runs locally.
*   **The AI Engine (Groq + Llama 3):** For complex, domain-specific fields that need human-like writing, such as **medical diagnoses**, **prescriptions**, **course descriptions**, or **product reviews**.

---

## 🚀 Key Features

*   🔍 **Schema & Relationship Aware:** The system reads your database tables, detects the connections between them (foreign keys), and figures out the exact order in which data must be created so that it doesn't break any database rules.
*   🧬 **AI Database Schema Assistant:** Don't have a database schema ready? Tell the AI what kind of business you are building (e.g., Healthcare, Education, E-commerce), and the AI will generate a complete database design for you.
*   ⚡ **Smart AI Caching:** To avoid calling the AI API repeatedly (which saves time and API limits), the system generates a pool of unique values per column and reuses them.
*   💾 **Instant Exports:** Once data is generated, you can download it as:
    *   **SQL Inserts:** Ready to be loaded straight into databases like PostgreSQL or MySQL.
    *   **CSV ZIP Archive:** Clean tables ready for Microsoft Excel or data analysis tools.
    *   **AI Summary Report:** A complete markdown file explaining the generation process, validation checks, and data statistics.

---

## 👥 Collaborative Team Contributions

This full-stack application was built collaboratively by a team of four, divided by project priorities:

1.  **🔴 Core Engine & Backend API:**
    *   Designed the FastAPI server, DDL parser, topological dependency resolver, and AI-Faker hybrid logic.
2.  **🟡 Frontend User Interface :**
    *   Designed the responsive web app using React, TanStack Start, and Tailwind CSS.
3.  **🟢 QA & Testing :**
    *   Built the comprehensive automated test suite (100 mocked AI and validator test cases).
4.  **🔵 Documentation & Video :**
    *   Responsible for project documentation, user guides, and demo demonstration preparation.

---

## 🛠️ Setup & Running Locally

### 1. Prerequisite Settings (`.env`)
Make sure you have your API key set up in `Project/backend/.env`. (Refer to `.env.example` to create this file).

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_groq_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
```

### 2. Start the Backend Server
Navigate to the backend directory, install Python dependencies, and run:

```bash
cd Project/backend
python -m venv venv
venv\Scripts\activate           # Windows command
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```
*Backend runs on: `http://localhost:8000`*

### 3. Start the Frontend Server
Open a new terminal, navigate to the frontend directory, and run:

```bash
cd Project/frontend
npm install
npm run dev
```
*Frontend runs on: `http://localhost:8080`*

---

## 💡 Quick 5-Minute Demo Flow

1.  Open the frontend URL: `http://localhost:8080`
2.  Go to **Schema Upload** and paste a simple 3-column SQL schema.
3.  Go to **AI Recommendation**, select a domain like "Healthcare", and click **Analyze**.
4.  The system will analyze and recommend AI Schema Regeneration. Click **Yes, regenerate schema**.
5.  On the **AI Schema Preview** screen, watch the Groq LLM generate a fully complete 6-to-8 table relational healthcare schema.
6.  Click **Use this AI-generated schema**.
7.  Go to **Data Generator**, choose "Hybrid AI+Faker Mode", and click **Generate**.
8.  Browse the generated data in the **Data Viewer** and check out the 🧠 symbols showing where AI populated complex medical details.
9.  Go to the **Export Center** to download your SQL inserts, CSV files, and AI reports!

---

## 🧪 Testing the Codebase

You can run the entire test suite locally to verify the code integrity. All AI requests are mocked, meaning you do not need an internet connection or an API key to run tests:

```bash
cd Project/backend
pytest
# 100/100 tests passed successfully!
```
