# AI Usage Note — v2 Upgrade

## How AI is Used

This project uses AI at **two distinct points** in the pipeline:

### 1. Schema Regeneration
- **When:** User provides a basic/generic schema and selects a domain.
- **What:** The AI generates a complete relational SQL DDL schema for the selected domain.
- **Model:** Gemini 1.5 Flash (free tier) / GPT-4o-mini / Llama via Groq.
- **Prompt strategy:** Domain-specific system prompt with original schema as context.
- **Validation:** Generated DDL is parsed and validated. One self-repair attempt on failure.

### 2. Hybrid Data Generation
- **When:** Schema contains domain-specific semantic fields.
- **What:** AI generates realistic text values for fields like `diagnosis`, `prescription`, `review_text`.
- **Strategy:** AI generates a pool of 20 values per column, cached. Each row picks from the pool randomly.
- **Not used for:** Primary keys, foreign keys, dates, numbers, emails, phones, status codes.

---

## What is NOT AI

The following use **pure Faker** (no AI):
- `name`, `email`, `phone`, `address`, `city`, `state`, `country`
- `date`, `created_at`, `updated_at`, `date_of_birth`
- `price`, `amount`, `total`, `salary`, `discount`
- `status`, `gender`, `type`
- `id`, primary keys, foreign keys

---

## Provider Options

| Provider | Free Tier | Setup |
|---|---|---|
| Google Gemini | ✅ 15 RPM free | Get key from aistudio.google.com |
| Groq | ✅ Free tier | Set OPENAI_BASE_URL to Groq URL |
| OpenAI | ❌ Paid | Add OPENAI_API_KEY |
| Fallback | ✅ Always | No key needed, Faker-only |

---

## Responsible AI Usage

- API keys are never hardcoded. All keys are loaded from `.env`.
- `.env` is in `.gitignore` — never committed to the repository.
- AI calls are minimized through caching (per domain + column name).
- AI is always optional — the system works fully without any AI provider.
- AI-generated content is synthetic only — not intended for production data.
