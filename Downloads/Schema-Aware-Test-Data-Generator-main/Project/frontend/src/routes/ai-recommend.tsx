import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Brain, Sparkles, Loader2, AlertCircle, CheckCircle2,
  ArrowRight, Zap, RefreshCw, ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import { classifySchema } from "@/lib/api";

export const Route = createFileRoute("/ai-recommend")({
  head: () => ({ meta: [{ title: "AI Recommendation · TestDataGen AI" }] }),
  component: AiRecommendPage,
});

const DOMAINS = [
  { id: "hospital", label: "Hospital Management", emoji: "🏥" },
  { id: "ecommerce", label: "E-Commerce", emoji: "🛒" },
  { id: "hospitality", label: "Hospitality / Hotel", emoji: "🏨" },
  { id: "banking", label: "Banking / Finance", emoji: "🏦" },
  { id: "education", label: "Education / Student", emoji: "🎓" },
  { id: "inventory", label: "Inventory Management", emoji: "📦" },
  { id: "crm", label: "CRM / Customer", emoji: "👥" },
  { id: "food_delivery", label: "Food Delivery", emoji: "🍕" },
  { id: "travel", label: "Travel Booking", emoji: "✈️" },
  { id: "general", label: "Custom / General", emoji: "⚙️" },
];

const COMPLEXITY_COLORS: Record<string, string> = {
  basic: "bg-amber-500/10 text-amber-700 border-amber-500/30",
  medium: "bg-blue-500/10 text-blue-700 border-blue-500/30",
  high: "bg-violet-500/10 text-violet-700 border-violet-500/30",
  domain_specific: "bg-emerald-500/10 text-emerald-700 border-emerald-500/30",
};

const REC_ICONS: Record<string, typeof Brain> = {
  faker_only: Zap,
  hybrid: Sparkles,
  ai_regeneration: Brain,
};

function AiRecommendPage() {
  const navigate = useNavigate();
  const {
    ddl, parsedSchema,
    selectedDomain, setSelectedDomain,
    setAiRegenerationAllowed,
    setClassificationResult,
    classificationResult,
  } = useStore();

  const [loading, setLoading] = useState(false);
  const [localDomain, setLocalDomain] = useState(selectedDomain || "");
  const [analyzed, setAnalyzed] = useState(!!classificationResult);

  async function handleAnalyze() {
    if (!ddl) {
      toast.error("No schema loaded. Upload a schema first.");
      return;
    }
    if (!localDomain) {
      toast.error("Please select a domain / use case.");
      return;
    }
    setLoading(true);
    try {
      const res = await classifySchema(ddl, localDomain);
      setSelectedDomain(localDomain);
      setClassificationResult({
        complexity: res.complexity as any,
        detected_domain: res.detected_domain,
        selected_domain: res.selected_domain,
        recommendation: res.recommendation as any,
        reason: res.reason,
        ai_columns: res.ai_columns,
        faker_columns: res.faker_columns,
      });
      setAnalyzed(true);
      toast.success("Schema classified successfully");
    } catch (err: any) {
      toast.error(err.message || "Classification failed");
    } finally {
      setLoading(false);
    }
  }

  function handleNoRegenerate() {
    setAiRegenerationAllowed(false);
    navigate({ to: "/generator" });
  }

  function handleYesRegenerate() {
    setAiRegenerationAllowed(true);
    navigate({ to: "/ai-schema-preview" });
  }

  const result = classificationResult;
  const RecIcon = result ? (REC_ICONS[result.recommendation] ?? Brain) : Brain;

  return (
    <AppShell
      title="AI Recommendation"
      description="Let the AI analyze your schema complexity and suggest the best generation strategy."
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

      {/* Step 1 — Domain selector */}
      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full gradient-brand text-white text-xs font-bold">1</span>
            Select your domain / use case
          </CardTitle>
          <CardDescription>
            Tell the AI what type of database this is for. This helps it suggest better data.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {DOMAINS.map((d) => {
              const active = localDomain === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setLocalDomain(d.id)}
                  className={`text-left rounded-xl border p-3.5 transition-all flex items-center gap-3 ${
                    active
                      ? "border-primary bg-primary/5 shadow-glow"
                      : "border-border/60 bg-card/60 hover:border-primary/40"
                  }`}
                >
                  <span className="text-xl">{d.emoji}</span>
                  <span className="font-medium text-sm">{d.label}</span>
                  {active && <CheckCircle2 className="h-4 w-4 text-primary ml-auto" />}
                </button>
              );
            })}
          </div>
          <div className="mt-4 flex items-center gap-3">
            <Button
              className="gradient-brand text-white border-0 shadow-glow"
              onClick={handleAnalyze}
              disabled={loading || !ddl || !localDomain}
            >
              {loading ? (
                <><Loader2 className="h-4 w-4 animate-spin mr-2" />Analyzing…</>
              ) : (
                <><Brain className="h-4 w-4 mr-2" />Analyze schema</>
              )}
            </Button>
            {analyzed && (
              <Button variant="outline" size="sm" onClick={() => { setAnalyzed(false); setClassificationResult(null); }}>
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Re-analyze
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Step 2 — Classification result */}
      {result && (
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Complexity + Domain cards */}
          <Card className="glass border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground uppercase tracking-wider">Schema Complexity</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className={`${COMPLEXITY_COLORS[result.complexity]} border text-sm px-3 py-1`}>
                {result.complexity.replace("_", " ")}
              </Badge>
            </CardContent>
          </Card>

          <Card className="glass border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground uppercase tracking-wider">Detected Domain</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <div className="font-medium capitalize">{result.detected_domain}</div>
              <div className="text-xs text-muted-foreground">Selected: <span className="font-medium capitalize">{result.selected_domain}</span></div>
            </CardContent>
          </Card>

          <Card className="glass border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-muted-foreground uppercase tracking-wider">AI Columns Detected</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="font-display text-2xl font-semibold">{result.ai_columns.length}</div>
              <div className="text-xs text-muted-foreground mt-0.5">columns needing semantic AI values</div>
            </CardContent>
          </Card>

          {/* Recommendation card */}
          <Card className="glass lg:col-span-3 border-border/50 overflow-hidden">
            <div className="h-1 w-full bg-gradient-to-r from-violet-500 to-blue-500" />
            <CardHeader className="flex flex-row items-start gap-4">
              <div className="h-12 w-12 shrink-0 rounded-xl gradient-brand flex items-center justify-center text-white shadow-md">
                <RecIcon className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-base">
                  {result.recommendation === "ai_regeneration" && "AI Schema Regeneration Recommended"}
                  {result.recommendation === "hybrid" && "Hybrid Faker + AI Generation Recommended"}
                  {result.recommendation === "faker_only" && "Faker-Only Generation Sufficient"}
                </CardTitle>
                <CardDescription className="mt-1 text-sm leading-relaxed">{result.reason}</CardDescription>
              </div>
            </CardHeader>

            {result.ai_columns.length > 0 && (
              <CardContent>
                <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  AI-generated fields preview
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {result.ai_columns.slice(0, 8).map((col) => (
                    <Badge key={col} variant="outline" className="font-mono text-[10px] border-violet-500/30 bg-violet-500/10 text-violet-700">
                      {col}
                    </Badge>
                  ))}
                  {result.ai_columns.length > 8 && (
                    <Badge variant="outline" className="text-[10px]">+{result.ai_columns.length - 8} more</Badge>
                  )}
                </div>
              </CardContent>
            )}
          </Card>

          {/* Ask user — AI regeneration offer (Always show so it's purely user optional) */}
          <Card className="glass lg:col-span-3 border-violet-500/30 bg-violet-500/5">
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex-1">
                  <div className="font-semibold text-sm mb-1">
                    Can I regenerate the schema for your use case?
                  </div>
                  <div className="text-xs text-muted-foreground">
                    The AI will create a complete{" "}
                    <span className="font-medium capitalize">{result.selected_domain || "selected"}</span> schema
                    with proper tables, relationships, and constraints. Or you can proceed with your original schema.
                  </div>
                </div>
                <div className="flex gap-3 shrink-0 flex-wrap">
                  <Button
                    size="sm"
                    className="gradient-brand text-white border-0 shadow-glow"
                    onClick={handleYesRegenerate}
                  >
                    <Sparkles className="h-4 w-4 mr-1.5" /> Yes, regenerate schema
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleNoRegenerate}
                  >
                    <ArrowRight className="h-4 w-4 mr-1.5" /> No, use my schema
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
