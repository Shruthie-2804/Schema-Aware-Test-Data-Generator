/**
 * api.ts
 * Central API service layer — extended for AI upgrade.
 * All fetch calls use VITE_API_BASE env variable.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// ── Utility ──────────────────────────────────────────────────────────────────
async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as any).detail || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Health ────────────────────────────────────────────────────────────────────
export async function checkHealth(): Promise<{ status: string; message: string; ai_provider: string; ai_available: boolean }> {
  const res = await fetch(`${API_BASE}/health`);
  return handleResponse(res);
}

// ── AI Status ─────────────────────────────────────────────────────────────────
export interface AIStatusResponse {
  provider: string;
  available: boolean;
  mode: string;
  note: string;
}

export async function getAiStatus(): Promise<AIStatusResponse> {
  const res = await fetch(`${API_BASE}/api/ai/status`);
  return handleResponse(res);
}

// ── Schema parse ──────────────────────────────────────────────────────────────
export interface ParsedTable {
  name: string;
  columns: { name: string; type: string; pk: boolean; fk: string | null }[];
  foreign_keys: string[];
}

export interface ParseSchemaResponse {
  success: boolean;
  tables: ParsedTable[];
  generation_order: string[];
  summary: string;
}

export async function parseSchema(ddl: string): Promise<ParseSchemaResponse> {
  const res = await fetch(`${API_BASE}/api/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ddl }),
  });
  return handleResponse(res);
}

// ── AI explain ────────────────────────────────────────────────────────────────
export interface ExplainSchemaResponse {
  success: boolean;
  explanation: string;
}

export async function explainSchema(ddl: string): Promise<ExplainSchemaResponse> {
  const res = await fetch(`${API_BASE}/api/ai/explain-schema`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ddl }),
  });
  return handleResponse(res);
}

// ── Classify schema ───────────────────────────────────────────────────────────
export interface ClassifySchemaResponse {
  success: boolean;
  complexity: string;
  detected_domain: string;
  selected_domain: string;
  recommendation: string;
  reason: string;
  ai_columns: string[];
  faker_columns: string[];
  domain_scores: Record<string, number>;
}

export async function classifySchema(ddlSchema: string, selectedDomain?: string): Promise<ClassifySchemaResponse> {
  const res = await fetch(`${API_BASE}/api/ai/classify-schema`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ddl_schema: ddlSchema, selected_domain: selectedDomain }),
  });
  return handleResponse(res);
}

// ── Regenerate schema (AI) ────────────────────────────────────────────────────
export interface RegenerateSchemaResponse {
  success: boolean;
  domain: string;
  generated_schema_sql: string;
  explanation: string;
  tables: string[];
  warnings: string[];
  provider_used: string;
}

export async function regenerateSchema(
  originalSchema: string,
  domain: string,
  userInstruction: string = '',
): Promise<RegenerateSchemaResponse> {
  const res = await fetch(`${API_BASE}/api/ai/regenerate-schema`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_schema: originalSchema,
      input_type: 'sql',
      domain,
      user_instruction: userInstruction,
      confirm_regeneration: true,
    }),
  });
  return handleResponse(res);
}

// ── Generate data (existing) ──────────────────────────────────────────────────
export interface GenerateDataResponse {
  success: boolean;
  generation_order: string[];
  all_data: Record<string, Record<string, unknown>[]>;
  passed: boolean;
  issues: string[];
  agent_log: string;
}

export async function generateData(ddl: string, numRows: number): Promise<GenerateDataResponse> {
  const res = await fetch(`${API_BASE}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ddl, num_rows: numRows }),
  });
  return handleResponse(res);
}

// ── Hybrid generate ───────────────────────────────────────────────────────────
export interface HybridGenerateResponse {
  success: boolean;
  generation_mode_used: string;
  faker_generated_fields: string[];
  ai_generated_fields: string[];
  data: Record<string, Record<string, unknown>[]>;
  provider_used: string;
  validation: { passed: boolean; issues: string[] };
  agent_log: string;
  downloads: { sql: string; csv: string; report: string };
}

export async function generateHybrid(
  ddlSchema: string,
  rowsPerTable: number,
  generationMode: 'auto' | 'faker_only' | 'hybrid',
  domain: string,
): Promise<HybridGenerateResponse> {
  const res = await fetch(`${API_BASE}/api/generate/hybrid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ddl_schema: ddlSchema,
      rows_per_table: rowsPerTable,
      generation_mode: generationMode,
      domain,
    }),
  });
  return handleResponse(res);
}

// ── Explain generation ────────────────────────────────────────────────────────
export interface ExplainGenerationResponse {
  success: boolean;
  explanation: string;
  generation_mode_used: string;
  faker_generated_fields: string[];
  ai_generated_fields: string[];
  ai_columns_count: number;
  faker_columns_count: number;
  validation_result: { passed: boolean; issues: string[]; issues_count: number };
}

export async function explainGeneration(params: {
  schema: string;
  domain: string;
  generationModeUsed: string;
  fakerGeneratedFields: string[];
  aiGeneratedFields: string[];
  validationPassed: boolean;
  validationIssues: string[];
}): Promise<ExplainGenerationResponse> {
  const res = await fetch(`${API_BASE}/api/ai/explain-generation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ddl_schema: params.schema,
      domain: params.domain,
      generation_mode_used: params.generationModeUsed,
      faker_generated_fields: params.fakerGeneratedFields,
      ai_generated_fields: params.aiGeneratedFields,
      validation_passed: params.validationPassed,
      validation_issues: params.validationIssues,
    }),
  });
  return handleResponse(res);
}

// ── Download helpers ──────────────────────────────────────────────────────────
export function getDownloadUrl(format: 'sql' | 'csv' | 'report'): string {
  return `${API_BASE}/api/download/${format}`;
}
