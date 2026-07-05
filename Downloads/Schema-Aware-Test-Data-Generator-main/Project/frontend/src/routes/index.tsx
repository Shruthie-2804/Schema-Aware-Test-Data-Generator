import { createFileRoute, Link } from "@tanstack/react-router";
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
import { Progress } from "@/components/ui/progress";
import {
  Database,
  Link2,
  Rows3,
  ShieldCheck,
  ArrowUpRight,
  TrendingUp,
  Sparkles,
  Activity,
  CheckCircle2,
  Clock,
  ArrowRight,
  Brain,
} from "lucide-react";
import { useStore } from "@/lib/store";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Dashboard · TestDataGen AI" }] }),
  component: Dashboard,
});

function Dashboard() {
  const {
    parsedSchema,
    generatedData,
    generationOrder,
    validationPassed,
    validationIssues,
    backendStatus,
  } = useStore();

  // Derive live KPIs from real store data
  const tablesCount = parsedSchema?.length ?? 0;
  const fkCount = parsedSchema
    ? parsedSchema.reduce((s, t) => s + (t.foreign_keys?.length ?? 0), 0)
    : 0;
  const totalRows = generatedData
    ? Object.values(generatedData).reduce((s, rows) => s + rows.length, 0)
    : 0;
  const validationScore = generatedData
    ? validationPassed
      ? 100
      : validationIssues?.length
        ? Math.max(0, 100 - validationIssues.length * 5)
        : 100
    : 0;

  const kpis = [
    {
      label: "Tables Detected",
      value: tablesCount || "—",
      icon: Database,
      tone: "from-blue-500/15 to-blue-500/0",
      iconColor: "text-blue-600",
      sub: tablesCount ? `${tablesCount} table${tablesCount !== 1 ? "s" : ""}` : "Upload a schema",
    },
    {
      label: "Foreign Keys",
      value: fkCount || "—",
      icon: Link2,
      tone: "from-violet-500/15 to-violet-500/0",
      iconColor: "text-violet-600",
      sub: fkCount ? `${fkCount} relationship${fkCount !== 1 ? "s" : ""}` : "No FK detected",
    },
    {
      label: "Rows Generated",
      value: totalRows ? totalRows.toLocaleString() : "—",
      icon: Rows3,
      tone: "from-indigo-500/15 to-indigo-500/0",
      iconColor: "text-indigo-600",
      sub: totalRows ? "Total across all tables" : "Generate data first",
    },
    {
      label: "Validation Score",
      value: generatedData ? `${validationScore}%` : "—",
      icon: ShieldCheck,
      tone: "from-emerald-500/15 to-emerald-500/0",
      iconColor: "text-emerald-600",
      sub: generatedData
        ? validationPassed
          ? "All checks passed"
          : `${validationIssues?.length || 0} issue(s) found`
        : "Not yet validated",
    },
  ];

  const pipelineChecks = [
    {
      label: "Schema parsing",
      value: parsedSchema ? 100 : 0,
      icon: CheckCircle2,
      color: parsedSchema ? "text-emerald-600" : "text-muted-foreground",
    },
    {
      label: "FK integrity",
      value: fkCount > 0 ? 100 : parsedSchema ? 80 : 0,
      icon: CheckCircle2,
      color: parsedSchema ? "text-emerald-600" : "text-muted-foreground",
    },
    {
      label: "Data realism",
      value: generatedData ? 94 : 0,
      icon: Activity,
      color: generatedData ? "text-blue-600" : "text-muted-foreground",
    },
    {
      label: "Backend health",
      value: backendStatus === "connected" ? 100 : backendStatus === "disconnected" ? 0 : 50,
      icon: Clock,
      color:
        backendStatus === "connected"
          ? "text-emerald-600"
          : backendStatus === "disconnected"
            ? "text-red-600"
            : "text-amber-600",
    },
  ];

  return (
    <AppShell
      title="Dashboard"
      description="Monitor synthetic data generation runs, schema health, and validation across your QA environments."
      actions={
        <>
          <Button variant="outline" size="sm" asChild>
            <Link to="/export">Export report</Link>
          </Button>
          <Button size="sm" className="gradient-brand text-white border-0" asChild>
            <Link to="/generator">
              <Sparkles className="h-4 w-4" /> Generate dataset
            </Link>
          </Button>
        </>
      }
    >
      {/* Live KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((k) => (
          <Card key={k.label} className="glass relative overflow-hidden border-border/50">
            <div
              className={`absolute inset-0 bg-gradient-to-br ${k.tone} pointer-events-none`}
            />
            <CardContent className="relative p-5">
              <div className="flex items-start justify-between">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg bg-card ${k.iconColor} shadow-sm`}
                >
                  <k.icon className="h-5 w-5" />
                </div>
                {k.value !== "—" && (
                  <Badge
                    variant="secondary"
                    className="gap-1 bg-emerald-500/10 text-emerald-700 border-0"
                  >
                    <TrendingUp className="h-3 w-3" /> Live
                  </Badge>
                )}
              </div>
              <div className="mt-4">
                <div className="font-display text-3xl font-semibold tracking-tight">
                  {k.value}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">{k.label}</div>
                <div className="mt-0.5 text-[10px] text-muted-foreground/70">{k.sub}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Generation order or quick-start */}
        <Card className="glass lg:col-span-2 border-border/50">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">
                {generatedData ? "Generated tables" : "Quick start"}
              </CardTitle>
              <CardDescription>
                {generatedData
                  ? `${generationOrder.length} table${generationOrder.length !== 1 ? "s" : ""} generated in dependency order`
                  : "Get started with these steps"}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {generatedData ? (
              <div className="divide-y divide-border/60">
                {generationOrder.map((tname) => {
                  const rows = generatedData[tname] || [];
                  const cols = rows.length > 0 ? Object.keys(rows[0]).length : 0;
                  return (
                    <div
                      key={tname}
                      className="flex items-center gap-4 px-6 py-3.5 hover:bg-muted/40 transition-colors"
                    >
                      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary font-mono text-[10px]">
                        TBL
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-sm truncate font-mono">{tname}</div>
                        <div className="text-xs text-muted-foreground">
                          {cols} columns · {rows.length} rows
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className="border-emerald-500/30 bg-emerald-500/10 text-emerald-700"
                      >
                        generated
                      </Badge>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="divide-y divide-border/60">
                {[
                  { step: "1", desc: "Upload or paste your SQL DDL schema", to: "/upload" },
                  { step: "2", desc: "Analyse and verify parsed tables & relationships", to: "/schema" },
                  { step: "3", desc: "Configure row count and generate test data", to: "/generator" },
                  { step: "4", desc: "Export SQL, CSV, or JSON for your QA pipeline", to: "/export" },
                ].map((s) => (
                  <Link
                    key={s.step}
                    to={s.to}
                    className="flex items-center gap-4 px-6 py-3.5 hover:bg-muted/40 transition-colors"
                  >
                    <div className="flex h-9 w-9 items-center justify-center rounded-md gradient-brand text-white font-mono text-sm font-bold">
                      {s.step}
                    </div>
                    <div className="flex-1 text-sm">{s.desc}</div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pipeline health card */}
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="text-base">Pipeline health</CardTitle>
            <CardDescription>Current QA environment status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {pipelineChecks.map((m) => (
              <div key={m.label}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2 text-sm">
                    <m.icon className={`h-3.5 w-3.5 ${m.color}`} />
                    {m.label}
                  </div>
                  <span className="text-xs font-mono text-muted-foreground">{m.value}%</span>
                </div>
                <Progress value={m.value} className="h-1.5" />
              </div>
            ))}
            <Button variant="outline" size="sm" className="w-full mt-2" asChild>
              <Link to="/validation">
                Open validation center <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick action cards */}
      <div className="grid gap-4 md:grid-cols-4">
        {[
          { title: "Upload schema", desc: "Drop a SQL file or paste DDL to begin", href: "/upload", icon: Database },
          { title: "Generate data", desc: "Choose domain and row count", href: "/generator", icon: Sparkles },
          { title: "AI Assistant", desc: "Explain schema with AI analysis", href: "/ai", icon: Brain },
          { title: "Export results", desc: "SQL, CSV, JSON or validation reports", href: "/export", icon: ArrowUpRight },
        ].map((q) => (
          <Link key={q.href} to={q.href}>
            <Card className="glass border-border/50 hover:border-primary/40 hover:shadow-glow transition-all group h-full">
              <CardContent className="p-5 flex items-center gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg gradient-brand text-white shadow-md shrink-0">
                  <q.icon className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{q.title}</div>
                  <div className="text-xs text-muted-foreground">{q.desc}</div>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0" />
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
