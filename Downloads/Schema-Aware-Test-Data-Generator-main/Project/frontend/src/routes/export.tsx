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
import { FileCode, FileSpreadsheet, FileText, Download, Clock, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import { getDownloadUrl } from "@/lib/api";

export const Route = createFileRoute("/export")({
  head: () => ({ meta: [{ title: "Export Center · TestDataGen AI" }] }),
  component: ExportPage,
});

const formats = [
  {
    id: "sql" as const,
    title: "Download SQL",
    desc: "INSERT statements respecting FK order. Ready to seed any RDBMS.",
    icon: FileCode,
    tag: "PostgreSQL · MySQL · SQL Server",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    id: "csv" as const,
    title: "Download CSV",
    desc: "One CSV per table, zipped together with a manifest.",
    icon: FileSpreadsheet,
    tag: "ZIP archive · UTF-8",
    gradient: "from-violet-500 to-fuchsia-500",
  },
  {
    id: "report" as const,
    title: "Download Report",
    desc: "Markdown validation summary with quality scores and check results.",
    icon: FileText,
    tag: "Markdown · share with QA leads",
    gradient: "from-emerald-500 to-teal-500",
  },
];

function ExportPage() {
  const { generatedData, generationOrder, parsedSchema } = useStore();

  const totalRows = generatedData
    ? Object.values(generatedData).reduce((s, rows) => s + rows.length, 0)
    : 0;

  const handleDownload = (format: (typeof formats)[number]) => {
    if (!generatedData) {
      toast.error("No data generated yet. Please generate data first.");
      return;
    }
    toast.success(`${format.title} download started`);
    window.open(getDownloadUrl(format.id), "_blank", "noreferrer");
  };

  return (
    <AppShell
      title="Export Center"
      description="Ship synthetic datasets and validation artifacts to QA, staging, and CI pipelines."
    >
      {/* Show warning if no data generated */}
      {!generatedData && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>
            No data generated yet.{" "}
            <Link to="/generator" className="font-semibold underline underline-offset-2">
              Generate a dataset first
            </Link>{" "}
            before downloading.
          </span>
        </div>
      )}

      {/* Summary stats */}
      {generatedData && (
        <div className="grid gap-3 sm:grid-cols-3 text-sm">
          <div className="rounded-lg border border-border/60 bg-card/60 px-4 py-3">
            <div className="text-xs text-muted-foreground">Tables</div>
            <div className="font-display text-2xl font-semibold">{parsedSchema?.length ?? generationOrder.length}</div>
          </div>
          <div className="rounded-lg border border-border/60 bg-card/60 px-4 py-3">
            <div className="text-xs text-muted-foreground">Total rows</div>
            <div className="font-display text-2xl font-semibold">{totalRows.toLocaleString()}</div>
          </div>
          <div className="rounded-lg border border-border/60 bg-card/60 px-4 py-3">
            <div className="text-xs text-muted-foreground">Formats available</div>
            <div className="font-display text-2xl font-semibold">3</div>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        {formats.map((f) => (
          <Card
            key={f.id}
            className="glass border-border/50 group hover:shadow-glow transition-all overflow-hidden"
          >
            <div className={`h-1 w-full bg-gradient-to-r ${f.gradient}`} />
            <CardHeader>
              <div
                className={`h-12 w-12 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center text-white shadow-md mb-3`}
              >
                <f.icon className="h-6 w-6" />
              </div>
              <CardTitle className="text-base">{f.title}</CardTitle>
              <CardDescription>{f.desc}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between text-xs">
                <Badge variant="outline" className="font-mono">
                  {f.tag}
                </Badge>
              </div>
              <Button
                className="w-full gradient-brand text-white border-0 cursor-pointer"
                onClick={() => handleDownload(f)}
                disabled={!generatedData}
              >
                <Download className="h-4 w-4 mr-2" /> Download
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* JSON client-side export */}
      {generatedData && (
        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Client-side JSON export
            </CardTitle>
            <CardDescription>
              Download the raw generated data as a JSON file directly from the browser.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => {
                const blob = new Blob([JSON.stringify(generatedData, null, 2)], {
                  type: "application/json",
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "generated_data.json";
                a.click();
                URL.revokeObjectURL(url);
                toast.success("JSON export downloaded");
              }}
            >
              <Download className="h-4 w-4" /> Export as JSON
            </Button>
          </CardContent>
        </Card>
      )}
    </AppShell>
  );
}
