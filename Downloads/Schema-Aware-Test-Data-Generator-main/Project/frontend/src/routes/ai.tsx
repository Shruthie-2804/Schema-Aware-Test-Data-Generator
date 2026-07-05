import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Brain, Loader2, AlertCircle, CheckCircle2, Copy } from "lucide-react";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import { explainSchema } from "@/lib/api";

export const Route = createFileRoute("/ai")({
  head: () => ({ meta: [{ title: "AI Schema Assistant · TestDataGen AI" }] }),
  component: AiPage,
});

function AiPage() {
  const { ddl, parsedSchema } = useStore();
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleExplain() {
    if (!ddl) {
      toast.error("No schema loaded. Please upload a schema first.");
      return;
    }
    setLoading(true);
    setError(null);
    setExplanation(null);
    try {
      const res = await explainSchema(ddl);
      setExplanation(res.explanation);
      toast.success("Schema explanation ready");
    } catch (err: any) {
      setError(err.message || "Failed to explain schema");
      toast.error(err.message || "Failed to explain schema");
    } finally {
      setLoading(false);
    }
  }

  function copyExplanation() {
    if (!explanation) return;
    navigator.clipboard.writeText(explanation);
    toast.success("Copied to clipboard");
  }

  return (
    <AppShell
      title="AI Schema Assistant"
      description="Use the built-in AI agent to explain your schema, identify relationships, and suggest improvements."
    >
      {/* No schema warning */}
      {!parsedSchema && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            No schema loaded.{" "}
            <Link to="/upload" className="font-semibold underline underline-offset-2">
              Upload a schema first
            </Link>{" "}
            before running AI analysis.
          </span>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Feature cards */}
        {[
          {
            icon: Brain,
            title: "Schema Understanding",
            desc: "The agent reads table names, column types, primary keys, and foreign keys to build a full relational map.",
            gradient: "from-violet-500 to-blue-500",
          },
          {
            icon: Sparkles,
            title: "Semantic Column Inference",
            desc: "Column names are matched against 40+ patterns to infer the correct data type (email, phone, date, price…).",
            gradient: "from-blue-500 to-cyan-500",
          },
          {
            icon: CheckCircle2,
            title: "Generation Order",
            desc: "The agent resolves FK dependencies topologically so parent tables are always generated before child tables.",
            gradient: "from-emerald-500 to-teal-500",
          },
        ].map((f) => (
          <Card key={f.title} className="glass border-border/50 overflow-hidden">
            <div className={`h-1 w-full bg-gradient-to-r ${f.gradient}`} />
            <CardContent className="p-5 flex gap-4">
              <div
                className={`h-11 w-11 shrink-0 rounded-lg bg-gradient-to-br ${f.gradient} flex items-center justify-center text-white shadow-md`}
              >
                <f.icon className="h-5 w-5" />
              </div>
              <div>
                <div className="font-semibold text-sm">{f.title}</div>
                <div className="text-xs text-muted-foreground mt-1">{f.desc}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Schema snapshot */}
      {parsedSchema && (
        <Card className="glass border-border/50">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">Loaded schema snapshot</CardTitle>
              <CardDescription>
                {parsedSchema.length} table{parsedSchema.length !== 1 ? "s" : ""} detected
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {parsedSchema.map((t) => (
                <Badge key={t.name} variant="secondary" className="font-mono text-[11px]">
                  {t.name}
                </Badge>
              ))}
            </div>
          </CardHeader>
        </Card>
      )}

      {/* Explain button */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            AI Explanation
          </CardTitle>
          <CardDescription>
            Click below to let the AI agent analyse your schema and return a plain-English explanation.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            className="gradient-brand text-white border-0 shadow-glow"
            onClick={handleExplain}
            disabled={loading || !ddl}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Analysing…
              </>
            ) : (
              <>
                <Brain className="h-4 w-4 mr-2" />
                Explain my schema
              </>
            )}
          </Button>

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          {explanation && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Badge
                  variant="outline"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-700 gap-1"
                >
                  <CheckCircle2 className="h-3 w-3" /> Analysis complete
                </Badge>
                <Button variant="ghost" size="sm" className="gap-1" onClick={copyExplanation}>
                  <Copy className="h-3.5 w-3.5" /> Copy
                </Button>
              </div>
              <pre className="whitespace-pre-wrap rounded-xl border border-border/60 bg-muted/40 p-5 text-sm leading-relaxed font-sans">
                {explanation}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </AppShell>
  );
}
