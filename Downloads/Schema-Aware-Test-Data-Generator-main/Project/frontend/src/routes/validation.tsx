import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Link2, Key, AlertTriangle, CheckCircle2, XCircle, RefreshCw, Terminal } from "lucide-react";
import { useStore } from "@/lib/store";

export const Route = createFileRoute("/validation")({
  head: () => ({ meta: [{ title: "Validation Center · TestDataGen AI" }] }),
  component: ValidationPage,
});

const statusCards = [
  { label: "Foreign Key Validation", value: "47/47", score: 100, icon: Link2, status: "pass", desc: "All references resolve correctly" },
  { label: "Primary Key Validation", value: "24/24", score: 100, icon: Key, status: "pass", desc: "No duplicates or nulls detected" },
  { label: "Data Quality Score", value: "98.6%", score: 98.6, icon: ShieldCheck, status: "pass", desc: "High realism across all domains" },
  { label: "Constraint Checks", value: "142/145", score: 97.9, icon: AlertTriangle, status: "warn", desc: "3 minor warnings to review" },
];

const checks = [
  { name: "customers.email uniqueness", category: "Unique constraint", status: "pass", rows: "250,000" },
  { name: "orders.customer_id → customers.id", category: "Foreign key", status: "pass", rows: "1,200,000" },
  { name: "order_items.order_id → orders.id", category: "Foreign key", status: "pass", rows: "4,820,000" },
  { name: "products.sku format", category: "Pattern match", status: "warn", rows: "12 anomalies" },
  { name: "orders.total range (>= 0)", category: "Check constraint", status: "pass", rows: "1,200,000" },
  { name: "customers.created_at chronology", category: "Temporal logic", status: "warn", rows: "2 outliers" },
  { name: "order_items.quantity > 0", category: "Check constraint", status: "fail", rows: "1 violation" },
];

function statusPill(s: string) {
  if (s === "pass") return <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-700 gap-1"><CheckCircle2 className="h-3 w-3" /> Passed</Badge>;
  if (s === "warn") return <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-amber-700 gap-1"><AlertTriangle className="h-3 w-3" /> Warning</Badge>;
  return <Badge variant="outline" className="border-red-500/30 bg-red-500/10 text-red-700 gap-1"><XCircle className="h-3 w-3" /> Failed</Badge>;
}

function ValidationPage() {
  const { validationPassed, validationIssues, agentLog, generatedData } = useStore();

  if (!generatedData) {
    return (
      <AppShell title="Validation Center" description="No data generated yet to validate.">
        <div className="p-12 text-center text-muted-foreground">Please generate data first to view validation results.</div>
      </AppShell>
    );
  }

  const dynamicCards = [
    { label: "Foreign Key Validation", value: validationPassed ? "Passed" : "Issues Found", score: validationPassed ? 100 : 50, icon: Link2, status: validationPassed ? "pass" : "fail", desc: "Checks referential integrity" },
    { label: "Data Quality Score", value: validationPassed ? "100%" : "Needs Review", score: validationPassed ? 100 : 70, icon: ShieldCheck, status: validationPassed ? "pass" : "warn", desc: "General data quality" },
  ];

  return (
    <AppShell
      title="Validation Center"
      description="Continuous integrity, uniqueness, and quality checks across generated datasets."
      actions={
        <Button variant="outline" size="sm"><RefreshCw className="h-4 w-4 mr-2" /> Re-run validation</Button>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {dynamicCards.map((c) => {
          const tone = c.status === "pass" ? "from-emerald-500/15" : c.status === "warn" ? "from-amber-500/15" : "from-red-500/15";
          const ic = c.status === "pass" ? "text-emerald-600" : c.status === "warn" ? "text-amber-600" : "text-red-600";
          return (
            <Card key={c.label} className="glass border-border/50 relative overflow-hidden">
              <div className={`absolute inset-0 bg-gradient-to-br ${tone} to-transparent pointer-events-none`} />
              <CardContent className="relative p-5">
                <div className={`h-10 w-10 rounded-lg bg-card flex items-center justify-center ${ic} shadow-sm`}>
                  <c.icon className="h-5 w-5" />
                </div>
                <div className="mt-4 font-display text-2xl font-semibold">{c.value}</div>
                <div className="text-xs font-medium">{c.label}</div>
                <div className="text-xs text-muted-foreground mt-1">{c.desc}</div>
                <Progress value={c.score} className="h-1 mt-3" />
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Validation Issues</CardTitle>
          <CardDescription>{validationIssues?.length || 0} issues detected during final checks</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {(!validationIssues || validationIssues.length === 0) ? (
            <div className="p-6 text-sm text-emerald-600 flex items-center gap-2 bg-emerald-500/5">
              <CheckCircle2 className="w-4 h-4" /> All checks passed perfectly!
            </div>
          ) : (
            <div className="divide-y divide-border/60">
              {validationIssues.map((issue: string, idx: number) => (
                <div key={idx} className="flex items-start gap-3 px-6 py-4 bg-red-500/5 text-red-700">
                  <XCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <div className="text-sm font-mono">{issue}</div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2"><Terminal className="w-4 h-4" /> Agent Generation Log</CardTitle>
          <CardDescription>Step-by-step reasoning from the AI agent</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="p-4 bg-black/90 text-lime-400 rounded-lg text-xs font-mono overflow-auto max-h-[400px] whitespace-pre-wrap">
            {agentLog || "No logs available."}
          </pre>
        </CardContent>
      </Card>
    </AppShell>
  );
}
