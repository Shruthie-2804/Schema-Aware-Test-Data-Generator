import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Sparkles, Zap, Brain, Loader2, AlertCircle,
  ShoppingBag, Landmark, Stethoscope, Users,
  Hotel, Package, HeartHandshake, Truck, Plane,
  Settings,
} from "lucide-react";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import { generateHybrid, generateData } from "@/lib/api";

export const Route = createFileRoute("/generator")({
  head: () => ({ meta: [{ title: "Data Generator · TestDataGen AI" }] }),
  component: GeneratorPage,
});

const DOMAINS = [
  { id: "ecommerce", name: "E-Commerce", icon: ShoppingBag, desc: "Customers, orders, products" },
  { id: "banking", name: "Banking", icon: Landmark, desc: "Accounts, transactions" },
  { id: "hospital", name: "Healthcare", icon: Stethoscope, desc: "Patients, doctors, appointments" },
  { id: "education", name: "Education", icon: Users, desc: "Students, courses, grades" },
  { id: "hospitality", name: "Hospitality", icon: Hotel, desc: "Hotels, bookings, guests" },
  { id: "inventory", name: "Inventory", icon: Package, desc: "Stock, suppliers, warehouses" },
  { id: "crm", name: "CRM", icon: HeartHandshake, desc: "Leads, contacts, campaigns" },
  { id: "food_delivery", name: "Food Delivery", icon: Truck, desc: "Restaurants, orders, riders" },
  { id: "travel", name: "Travel", icon: Plane, desc: "Flights, bookings, packages" },
  { id: "general", name: "General", icon: Settings, desc: "Auto-detect or custom" },
];

const GENERATION_MODES = [
  { id: "auto", label: "Auto", desc: "System decides based on schema complexity", icon: Sparkles },
  { id: "faker_only", label: "Faker Only", desc: "Fast, free, no AI calls", icon: Zap },
  { id: "hybrid", label: "Hybrid AI+Faker", desc: "Faker + AI for semantic fields", icon: Brain },
];

function GeneratorPage() {
  const {
    ddl, parsedSchema,
    selectedDomain, setSelectedDomain,
    setGeneratedData, setAgentLog, setValidationIssues, setValidationPassed,
    setGenerationModeUsed, setFakerGeneratedFields, setAiGeneratedFields,
    aiProviderAvailable,
    classificationResult,
    aiSchemaConfirmed,
  } = useStore();
  const navigate = useNavigate();

  const [rows, setRows] = useState([10]);
  const [localDomain, setLocalDomain] = useState(selectedDomain || "general");
  const [genMode, setGenMode] = useState<"auto" | "faker_only" | "hybrid">("auto");
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);

  const tablesCount = parsedSchema?.length ?? 0;

  async function generate() {
    if (!ddl) {
      toast.error("No schema found. Please upload one first.");
      navigate({ to: "/upload" });
      return;
    }
    setGenerating(true);
    setProgress(5);
    setSelectedDomain(localDomain);

    const interval = setInterval(() => {
      setProgress((p) => (p < 85 ? p + 5 : p));
    }, 500);

    try {
      // Use hybrid endpoint for all generations (it handles faker_only too)
      const res = await generateHybrid(ddl, rows[0], genMode, localDomain);
      clearInterval(interval);
      setProgress(100);

      setGeneratedData(res.data);
      setAgentLog(res.agent_log);
      setValidationIssues(res.validation.issues);
      setValidationPassed(res.validation.passed);
      setGenerationModeUsed(res.generation_mode_used);
      setFakerGeneratedFields(res.faker_generated_fields);
      setAiGeneratedFields(res.ai_generated_fields);

      const modeLabel = res.generation_mode_used === "hybrid"
        ? `Hybrid (${res.ai_generated_fields.length} AI fields)`
        : "Faker-only";
      toast.success(`Dataset generated · ${modeLabel}`);
      setTimeout(() => navigate({ to: "/data" }), 500);
    } catch (err: any) {
      clearInterval(interval);
      toast.error(err.message || "Failed to generate data");
      setGenerating(false);
      setProgress(0);
    }
  }

  return (
    <AppShell
      title="Data Generator"
      description="Configure synthetic data generation with domain-aware realism and referential integrity."
    >
      {!parsedSchema && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            No schema loaded.{" "}
            <Link to="/upload" className="font-semibold underline underline-offset-2">
              Upload a schema first
            </Link>
          </span>
        </div>
      )}

      {/* AI schema confirmation banner */}
      {aiSchemaConfirmed && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-700">
          <Brain className="h-5 w-5 shrink-0" />
          <span>Using <strong>AI-generated schema</strong>. You can change the generation mode below.</span>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {/* Domain selector */}
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="text-base">Domain template</CardTitle>
              <CardDescription>
                Pick a domain to tune generation realism and enable AI features.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2.5 sm:grid-cols-2">
                {DOMAINS.map((d) => {
                  const active = localDomain === d.id;
                  return (
                    <button
                      key={d.id}
                      onClick={() => setLocalDomain(d.id)}
                      className={`text-left rounded-xl border p-3.5 transition-all ${
                        active
                          ? "border-primary bg-primary/5 shadow-glow"
                          : "border-border/60 bg-card/60 hover:border-primary/40"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${
                          active ? "gradient-brand text-white" : "bg-muted text-foreground"
                        }`}>
                          <d.icon className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-medium text-sm">{d.name}</div>
                          <div className="text-xs text-muted-foreground">{d.desc}</div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Generation mode */}
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="text-base">Generation mode</CardTitle>
              <CardDescription>
                Choose how data is generated. Hybrid uses AI for semantic fields.
                {!aiProviderAvailable && (
                  <span className="text-amber-600 font-medium ml-1">
                    · AI provider not configured — Hybrid will fall back to Faker-only.
                  </span>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2.5 sm:grid-cols-3">
                {GENERATION_MODES.map((m) => {
                  const active = genMode === m.id;
                  return (
                    <button
                      key={m.id}
                      onClick={() => setGenMode(m.id as any)}
                      className={`text-left rounded-xl border p-3.5 transition-all ${
                        active
                          ? "border-primary bg-primary/5 shadow-glow"
                          : "border-border/60 bg-card/60 hover:border-primary/40"
                      }`}
                    >
                      <div className={`h-8 w-8 rounded-lg flex items-center justify-center mb-2 ${
                        active ? "gradient-brand text-white" : "bg-muted text-foreground"
                      }`}>
                        <m.icon className="h-4 w-4" />
                      </div>
                      <div className="font-medium text-sm">{m.label}</div>
                      <div className="text-[11px] text-muted-foreground mt-0.5">{m.desc}</div>
                    </button>
                  );
                })}
              </div>

              {/* AI column preview from classification */}
              {classificationResult && classificationResult.ai_columns.length > 0 && genMode !== "faker_only" && (
                <div className="mt-4 p-3 rounded-lg border border-violet-500/30 bg-violet-500/5">
                  <div className="text-xs font-medium text-violet-700 mb-1.5">
                    AI will generate values for these fields:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {classificationResult.ai_columns.slice(0, 6).map((c) => (
                      <Badge key={c} variant="outline" className="font-mono text-[10px] border-violet-500/30 text-violet-700">
                        {c.split(".")[1] || c}
                      </Badge>
                    ))}
                    {classificationResult.ai_columns.length > 6 && (
                      <Badge variant="outline" className="text-[10px]">
                        +{classificationResult.ai_columns.length - 6} more
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Volume options */}
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="text-base">Volume & options</CardTitle>
              <CardDescription>Tune row counts and generation behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <Label className="text-sm">Row count per table</Label>
                  <Badge variant="outline" className="font-mono">{rows[0].toLocaleString()} rows</Badge>
                </div>
                <Slider value={rows} onValueChange={setRows} min={1} max={500} step={1} />
                <div className="mt-2 flex justify-between text-[10px] text-muted-foreground font-mono">
                  <span>1</span><span>100</span><span>250</span><span>500</span>
                </div>
              </div>

              <div className="space-y-3">
                {[
                  { label: "Preserve referential integrity", checked: true },
                  { label: "Run validation after generation", checked: true },
                ].map((o) => (
                  <div key={o.label} className="flex items-center justify-between rounded-lg border border-border/60 bg-card/60 px-4 py-2.5">
                    <span className="text-sm">{o.label}</span>
                    <Switch defaultChecked={o.checked} />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Summary panel */}
        <Card className="glass border-border/50 h-fit sticky top-20">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" /> Generation summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Domain</span>
                <span className="font-medium capitalize">{DOMAINS.find(d => d.id === localDomain)?.name ?? localDomain}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mode</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {genMode === "auto" ? "auto" : genMode === "hybrid" ? "Faker+AI" : "Faker only"}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tables</span>
                <span className="font-medium">{tablesCount || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Rows / table</span>
                <span className="font-mono">{rows[0].toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Est. total rows</span>
                <span className="font-mono">{(rows[0] * (tablesCount || 1)).toLocaleString()}</span>
              </div>
              {classificationResult && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">AI fields</span>
                  <Badge variant="outline" className="text-[10px] border-violet-500/30 bg-violet-500/10 text-violet-700">
                    {classificationResult.ai_columns.length} cols
                  </Badge>
                </div>
              )}
            </div>

            {generating && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-muted-foreground">Generating…</span>
                  <span className="font-mono">{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}

            <Button
              size="lg"
              className="w-full gradient-brand text-white border-0 shadow-glow"
              onClick={generate}
              disabled={generating || !ddl}
            >
              <Zap className="h-4 w-4" />
              {generating ? "Generating…" : "Generate dataset"}
            </Button>

            {/* AI recommend shortcut */}
            {!classificationResult && (
              <Button
                variant="outline"
                size="sm"
                className="w-full gap-1.5"
                asChild
              >
                <a href="/ai-recommend">
                  <Brain className="h-3.5 w-3.5" />
                  Get AI recommendation
                </a>
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
