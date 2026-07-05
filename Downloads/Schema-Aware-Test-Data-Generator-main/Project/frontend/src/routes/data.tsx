import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useStore } from "@/lib/store";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, ChevronLeft, ChevronRight, Download, Brain, Zap } from "lucide-react";

export const Route = createFileRoute("/data")({
  head: () => ({ meta: [{ title: "Data Viewer · TestDataGen AI" }] }),
  component: DataPage,
});

function DataTable({ rows, cols, aiFields }: { rows: Record<string, unknown>[]; cols: string[]; aiFields: string[] }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const filtered = useMemo(
    () => rows.filter((r) => cols.some((c) => String(r[c]).toLowerCase().includes(search.toLowerCase()))),
    [rows, cols, search]
  );
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const view = filtered.slice((page - 1) * pageSize, page * pageSize);

  return (
    <>
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search rows…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9 h-9 bg-background/60"
          />
        </div>
        <div className="text-xs text-muted-foreground font-mono">
          {filtered.length.toLocaleString()} rows
        </div>
      </div>

      <div className="rounded-lg border border-border/60 overflow-hidden bg-card/40">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              {cols.map((c) => (
                <TableHead key={c} className="font-mono text-[11px] uppercase tracking-wider">
                  <div className="flex items-center gap-1.5">
                    {c}
                    {aiFields.includes(c) ? (
                      <Brain className="h-3 w-3 text-violet-500" title="AI-generated" />
                    ) : (
                      <Zap className="h-3 w-3 text-blue-400 opacity-50" title="Faker-generated" />
                    )}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {view.map((r, i) => (
              <TableRow key={i}>
                {cols.map((c) => (
                  <TableCell key={c} className="font-mono text-xs max-w-[200px] truncate">
                    {c === "status" ? (
                      <Badge variant="outline" className="capitalize">{String(r[c])}</Badge>
                    ) : (
                      String(r[c] ?? "")
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <span className="text-xs text-muted-foreground">
          Page {page} of {totalPages}
        </span>
        <div className="flex gap-1">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>
            <ChevronLeft className="h-3.5 w-3.5" />
          </Button>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </>
  );
}

function DataPage() {
  const { generatedData, generationOrder, generationModeUsed, aiGeneratedFields, fakerGeneratedFields, selectedDomain } = useStore();
  
  const tabs = useMemo(() => {
    if (!generatedData) return [];
    return generationOrder.map((tname: string) => {
      const rows = generatedData[tname] || [];
      const cols = rows.length > 0 ? Object.keys(rows[0]) : [];
      const tableAiFields = aiGeneratedFields
        .filter((f) => f.startsWith(`${tname}.`))
        .map((f) => f.split(".")[1]);
      return { id: tname, label: tname, rows, cols, tableAiFields };
    });
  }, [generatedData, generationOrder, aiGeneratedFields]);

  if (!generatedData || tabs.length === 0) {
    return (
      <AppShell title="Generated Data Viewer" description="No data available.">
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <h3 className="text-lg font-semibold">No Generated Data</h3>
          <p className="text-sm text-muted-foreground mb-6">Please generate data first.</p>
          <Link to="/generator">
            <Button>Go to Generator</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      title="Generated Data Viewer"
      description="Inspect generated rows across tables. Purple brain icon = AI-generated field."
      actions={
        <Link to="/export">
          <Button size="sm" variant="outline"><Download className="h-4 w-4 mr-2" /> Export</Button>
        </Link>
      }
    >
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-4 py-2.5 text-sm">
          <span className="text-muted-foreground">Mode:</span>
          <Badge variant="outline" className="font-mono text-xs capitalize">
            {generationModeUsed?.replace("_", " ") ?? "N/A"}
          </Badge>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-4 py-2.5 text-sm">
          <Zap className="h-3.5 w-3.5 text-blue-400" />
          <span className="text-muted-foreground">Faker fields:</span>
          <span className="font-medium">{fakerGeneratedFields.length}</span>
        </div>
        {aiGeneratedFields.length > 0 && (
          <div className="flex items-center gap-2 rounded-lg border border-violet-500/30 bg-violet-500/10 px-4 py-2.5 text-sm">
            <Brain className="h-3.5 w-3.5 text-violet-500" />
            <span className="text-violet-700">AI fields:</span>
            <span className="font-medium text-violet-700">{aiGeneratedFields.length}</span>
          </div>
        )}
        {selectedDomain && (
          <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-card/60 px-4 py-2.5 text-sm">
            <span className="text-muted-foreground">Domain:</span>
            <span className="font-medium capitalize">{selectedDomain}</span>
          </div>
        )}
      </div>

      {aiGeneratedFields.length > 0 && (
        <Card className="glass border-violet-500/30 bg-violet-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Brain className="h-4 w-4 text-violet-500" />
              AI-generated columns
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1.5">
              {aiGeneratedFields.map((f) => (
                <Badge key={f} variant="outline" className="font-mono text-[10px] border-violet-500/30 bg-violet-500/10 text-violet-700">
                  {f}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="glass border-border/50">
        <CardContent className="p-5">
          <Tabs defaultValue={tabs[0]?.id}>
            <TabsList className="mb-4 flex-wrap">
              {tabs.map((t: any) => (
                <TabsTrigger key={t.id} value={t.id}>
                  <span className="font-mono">{t.label}</span>
                  <Badge variant="secondary" className="ml-2">{t.rows.length}</Badge>
                  {t.tableAiFields.length > 0 && (
                    <Brain className="h-3 w-3 text-violet-500 ml-1" />
                  )}
                </TabsTrigger>
              ))}
            </TabsList>
            {tabs.map((t: any) => (
              <TabsContent key={t.id} value={t.id} className="mt-4">
                <DataTable rows={t.rows} cols={t.cols} aiFields={t.tableAiFields} />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </AppShell>
  );
}
