import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { AppShell } from "@/components/AppShell";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Brain, Sparkles, Loader2, AlertCircle, CheckCircle2,
  Copy, ArrowLeft, ArrowRight, Edit3, RotateCcw, Database,
} from "lucide-react";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import { regenerateSchema, parseSchema } from "@/lib/api";

export const Route = createFileRoute("/ai-schema-preview")({
  head: () => ({ meta: [{ title: "AI Schema Preview · TestDataGen AI" }] }),
  component: AiSchemaPreviewPage,
});

function AiSchemaPreviewPage() {
  const navigate = useNavigate();
  const {
    ddl, setDdl, selectedDomain,
    aiRegeneratedSchema, setAiRegeneratedSchema,
    setAiSchemaConfirmed,
    setParsedSchema, setGenerationOrder, setSchemaSummary,
  } = useStore();

  const [loading, setLoading] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [editedSql, setEditedSql] = useState("");
  const [applyLoading, setApplyLoading] = useState(false);

  // Auto-generate on mount if no result yet
  useEffect(() => {
    if (!aiRegeneratedSchema && ddl && selectedDomain) {
      handleRegenerate();
    }
  }, []);

  async function handleRegenerate() {
    if (!ddl || !selectedDomain) {
      toast.error("No schema or domain selected. Go back.");
      return;
    }
    setLoading(true);
    setAiRegeneratedSchema(null);
    try {
      const result = await regenerateSchema(ddl, selectedDomain, instruction);
      setAiRegeneratedSchema(result);
      if (result.success) {
        setEditedSql(result.generated_schema_sql);
        toast.success("AI schema generated successfully");
      } else {
        toast.error(result.warnings[0] || "AI generation failed");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to call AI regeneration");
    } finally {
      setLoading(false);
    }
  }

  async function handleUseThisSchema() {
    const sqlToApply = editMode ? editedSql : aiRegeneratedSchema?.generated_schema_sql;
    if (!sqlToApply) return;
    setApplyLoading(true);
    try {
      const parsed = await parseSchema(sqlToApply);
      setDdl(sqlToApply);
      setParsedSchema(parsed.tables);
      setGenerationOrder(parsed.generation_order);
      setSchemaSummary(parsed.summary || "");
      setAiSchemaConfirmed(true);
      toast.success("AI-generated schema applied! Ready to generate data.");
      navigate({ to: "/generator" });
    } catch (err: any) {
      toast.error(err.message || "Failed to parse AI-generated schema. Try editing it.");
    } finally {
      setApplyLoading(false);
    }
  }

  function handleGoBackToOriginal() {
    setAiSchemaConfirmed(false);
    navigate({ to: "/generator" });
  }

  function copySchema() {
    const sql = editMode ? editedSql : aiRegeneratedSchema?.generated_schema_sql;
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    toast.success("Schema copied to clipboard");
  }

  const result = aiRegeneratedSchema;

  return (
    <AppShell
      title="AI Schema Preview"
      description="Review the AI-generated schema before applying it. You can edit, regenerate, or go back to your original schema."
    >
      {/* Warning if no domain selected */}
      {!selectedDomain && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            No domain selected.{" "}
            <Link to="/ai-recommend" className="font-semibold underline">
              Go back to AI Recommendation
            </Link>
          </span>
        </div>
      )}

      {/* Instruction card */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            AI Schema Generator
          </CardTitle>
          <CardDescription>
            Generating schema for:{" "}
            <span className="font-semibold capitalize">{selectedDomain || "—"}</span>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label className="text-sm mb-1.5 block">
              Optional: Add specific instructions for the AI
            </Label>
            <Textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="e.g., Include billing and insurance tables. Add audit timestamps to all tables."
              className="min-h-[80px] text-sm font-mono bg-background/60"
            />
          </div>
          <Button
            className="gradient-brand text-white border-0 shadow-glow"
            onClick={handleRegenerate}
            disabled={loading || !ddl || !selectedDomain}
          >
            {loading ? (
              <><Loader2 className="h-4 w-4 animate-spin mr-2" />Generating…</>
            ) : (
              <><Brain className="h-4 w-4 mr-2" />
                {result ? "Regenerate schema" : "Generate schema"}
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Loading state */}
      {loading && (
        <Card className="glass border-border/50">
          <CardContent className="p-8 flex flex-col items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl gradient-brand text-white shadow-glow">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
            <div className="text-center">
              <div className="font-semibold">AI is generating your schema…</div>
              <div className="text-xs text-muted-foreground mt-1">
                This may take 10–30 seconds depending on the AI provider.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error / fallback */}
      {result && !result.success && (
        <Card className="glass border-red-500/30 bg-red-500/5">
          <CardContent className="p-5 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-sm text-red-700">AI generation failed</div>
              {result.warnings.map((w, i) => (
                <div key={i} className="text-xs text-red-600 mt-1">{w}</div>
              ))}
              <div className="text-xs text-muted-foreground mt-2">
                You can continue with your original schema.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success — schema preview */}
      {result?.success && (
        <>
          {/* Meta info row */}
          <div className="grid gap-3 sm:grid-cols-3">
            <Card className="glass border-border/50">
              <CardContent className="p-4">
                <div className="text-xs text-muted-foreground">Provider used</div>
                <div className="font-mono text-sm mt-0.5">{result.provider_used}</div>
              </CardContent>
            </Card>
            <Card className="glass border-border/50">
              <CardContent className="p-4">
                <div className="text-xs text-muted-foreground">Tables generated</div>
                <div className="font-display text-2xl font-semibold">{result.tables.length}</div>
              </CardContent>
            </Card>
            <Card className="glass border-border/50">
              <CardContent className="p-4">
                <div className="text-xs text-muted-foreground">Domain</div>
                <div className="font-medium capitalize mt-0.5">{result.domain}</div>
              </CardContent>
            </Card>
          </div>

          {/* Explanation */}
          {result.explanation && (
            <Card className="glass border-border/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Brain className="h-4 w-4 text-violet-500" /> AI Explanation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground leading-relaxed">{result.explanation}</p>
              </CardContent>
            </Card>
          )}

          {/* Table list */}
          <Card className="glass border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Database className="h-4 w-4 text-blue-500" /> Tables & Relationships
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {result.tables.map((t) => (
                  <Badge key={t} variant="secondary" className="font-mono text-xs">
                    {t}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <div className="text-xs font-medium text-amber-700 mb-1">Warnings</div>
              {result.warnings.map((w, i) => (
                <div key={i} className="text-xs text-amber-600">• {w}</div>
              ))}
            </div>
          )}

          {/* SQL Preview / Edit */}
          <Card className="glass border-border/50">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm">
                {editMode ? "Edit schema" : "Generated SQL DDL"}
              </CardTitle>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1.5"
                  onClick={() => { setEditMode(!editMode); if (!editMode) setEditedSql(result.generated_schema_sql); }}
                >
                  <Edit3 className="h-3.5 w-3.5" />
                  {editMode ? "Preview" : "Edit"}
                </Button>
                <Button variant="ghost" size="sm" className="gap-1.5" onClick={copySchema}>
                  <Copy className="h-3.5 w-3.5" /> Copy
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {editMode ? (
                <Textarea
                  value={editedSql}
                  onChange={(e) => setEditedSql(e.target.value)}
                  className="font-mono text-xs min-h-[400px] bg-background/60"
                />
              ) : (
                <pre className="whitespace-pre-wrap text-xs font-mono leading-relaxed rounded-xl border border-border/60 bg-muted/40 p-5 max-h-[400px] overflow-auto">
                  {result.generated_schema_sql}
                </pre>
              )}
            </CardContent>
          </Card>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-3">
            <Button
              className="gradient-brand text-white border-0 shadow-glow"
              onClick={handleUseThisSchema}
              disabled={applyLoading}
            >
              {applyLoading
                ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />Applying…</>
                : <><CheckCircle2 className="h-4 w-4 mr-2" />Use this AI-generated schema</>
              }
            </Button>
            <Button variant="outline" onClick={handleRegenerate} disabled={loading}>
              <RotateCcw className="h-4 w-4 mr-1.5" /> Regenerate
            </Button>
            <Button variant="outline" onClick={handleGoBackToOriginal}>
              <ArrowLeft className="h-4 w-4 mr-1.5" /> Use my original schema
            </Button>
          </div>
        </>
      )}

      {/* Navigation if no result yet */}
      {!result && !loading && (
        <div className="flex gap-3">
          <Button variant="outline" asChild>
            <Link to="/ai-recommend">
              <ArrowLeft className="h-4 w-4 mr-1.5" /> Back to domain selection
            </Link>
          </Button>
        </div>
      )}
    </AppShell>
  );
}
