import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Accordion, AccordionItem, AccordionTrigger, AccordionContent,
} from "@/components/ui/accordion";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Database, Key, Link2, ArrowRight, Brain, Sparkles } from "lucide-react";

export const Route = createFileRoute("/schema")({
  head: () => ({ meta: [{ title: "Schema Analysis · TestDataGen AI" }] }),
  component: SchemaPage,
});

import { useStore } from "@/lib/store";
import { Button } from "@/components/ui/button";


function keyBadge(k: string) {
  if (!k) return null;
  const map: Record<string, string> = {
    PK: "border-violet-500/30 bg-violet-500/10 text-violet-700",
    FK: "border-blue-500/30 bg-blue-500/10 text-blue-700",
    UQ: "border-amber-500/30 bg-amber-500/10 text-amber-700",
  };
  return <Badge variant="outline" className={`${map[k]} font-mono text-[10px]`}>{k}</Badge>;
}

function GraphNode({ name, color = "from-blue-500 to-violet-500" }: { name: string; color?: string }) {
  return (
    <div className={`relative rounded-xl bg-gradient-to-br ${color} p-[1px] shadow-md`}>
      <div className="rounded-[11px] bg-card px-4 py-3 min-w-[140px] text-center">
        <Database className="h-4 w-4 mx-auto text-primary mb-1" />
        <div className="font-mono text-xs font-semibold">{name}</div>
      </div>
    </div>
  );
}

function SchemaPage() {
  const { parsedSchema, generationOrder, schemaSummary } = useStore();
  const tables = parsedSchema || [];
  
  if (tables.length === 0) {
    return (
      <AppShell title="Schema Analysis" description="No schema loaded. Please upload a schema first.">
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <Database className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold">No Schema Data</h3>
          <p className="text-sm text-muted-foreground mb-6">Upload or paste your SQL DDL to analyze the schema.</p>
          <Link to="/upload">
            <Button>Go to Upload</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const fksCount = tables.reduce((s: number, t: any) => s + (t.foreign_keys?.length || 0), 0);
  const pksCount = tables.reduce((s: number, t: any) => s + t.columns.filter((c: any) => c.pk).length, 0);

  return (
    <AppShell
      title="Schema Analysis"
      description="Parsed tables, columns, and referential relationships from your uploaded schema."
      actions={
        <Button size="sm" className="gap-1" asChild>
          <Link to="/ai"><Brain className="h-4 w-4" /> AI Explain</Link>
        </Button>
      }
    >
      <div className="grid gap-4 lg:grid-cols-3">
        {[
          { label: "Tables", value: tables.length, icon: Database },
          { label: "Foreign Keys", value: fksCount, icon: Link2 },
          { label: "Primary Keys", value: pksCount, icon: Key },
        ].map((s) => (
          <Card key={s.label} className="glass border-border/50">
            <CardContent className="p-5 flex items-center gap-4">
              <div className="h-11 w-11 rounded-lg gradient-brand flex items-center justify-center text-white shadow-md">
                <s.icon className="h-5 w-5" />
              </div>
              <div>
                <div className="font-display text-2xl font-semibold">{s.value}</div>
                <div className="text-xs text-muted-foreground">{s.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="glass border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Dependency graph</CardTitle>
          <CardDescription>Generation order respects referential integrity</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl border border-border/60 bg-gradient-to-br from-muted/30 to-transparent p-8 overflow-x-auto">
            <div className="flex items-center justify-center gap-6 min-w-max">
              {generationOrder.map((tableName: string, idx: number) => (
                <div key={tableName} className="flex items-center gap-6">
                  <GraphNode name={tableName} color={idx % 2 === 0 ? "from-blue-500 to-cyan-500" : "from-violet-500 to-blue-500"} />
                  {idx < generationOrder.length - 1 && <ArrowRight className="h-5 w-5 text-muted-foreground shrink-0" />}
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="glass border-border/50 lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Tables & columns</CardTitle>
            <CardDescription>Expand each table to view its columns</CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" defaultValue={tables.length > 0 ? [tables[0].name] : []} className="space-y-2">
              {tables.map((t: any) => (
                <AccordionItem key={t.name} value={t.name} className="rounded-lg border border-border/60 bg-card/60 px-4">
                  <AccordionTrigger className="hover:no-underline py-3">
                    <div className="flex items-center gap-3 flex-1">
                      <Database className="h-4 w-4 text-primary" />
                      <span className="font-mono text-sm font-semibold">{t.name}</span>
                      <Badge variant="secondary" className="ml-auto">{t.columns.length} cols</Badge>
                      {t.foreign_keys?.length > 0 && (
                        <Badge variant="outline" className="border-blue-500/30 bg-blue-500/10 text-blue-700">
                          {t.foreign_keys.length} FK
                        </Badge>
                      )}
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Column</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Key</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {t.columns.map((c: any) => (
                          <TableRow key={c.name}>
                            <TableCell className="font-mono text-xs">{c.name}</TableCell>
                            <TableCell className="font-mono text-xs text-muted-foreground">{c.type}</TableCell>
                            <TableCell>{keyBadge(c.pk ? "PK" : c.fk ? "FK" : "")}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>

        <Card className="glass border-border/50">
          <CardHeader>
            <CardTitle className="text-base">Foreign key relationships</CardTitle>
            <CardDescription>All cross-table references</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {tables.flatMap((t: any) =>
              (t.columns || []).filter((c: any) => c.fk).map((c: any) => (
                <div key={`${t.name}.${c.name}`} className="rounded-lg border border-border/60 bg-card/60 p-3">
                  <div className="flex items-center gap-2 text-xs font-mono">
                    <span className="text-foreground">{t.name}.{c.name}</span>
                    <ArrowRight className="h-3 w-3 text-primary" />
                    <span className="text-muted-foreground">{c.fk}</span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
