import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useRef } from "react";
import { AppShell } from "@/components/AppShell";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Upload, FileCode, CheckCircle2, FileText, X, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useStore } from "@/lib/store";
import { parseSchema } from "@/lib/api";

export const Route = createFileRoute("/upload")({
  head: () => ({ meta: [{ title: "Schema Upload · TestDataGen AI" }] }),
  component: UploadPage,
});

const SAMPLE = `CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(120),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(id),
  total NUMERIC(10,2),
  status VARCHAR(32),
  placed_at TIMESTAMP
);`;

function UploadPage() {
  const navigate = useNavigate();
  const { setDdl, setParsedSchema, setGenerationOrder, setSchemaSummary } = useStore();
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<{ name: string; size: string }[]>([]);
  const [sql, setSql] = useState(SAMPLE);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target?.result as string;
      setSql(text);
      const sizeKb = (file.size / 1024).toFixed(1) + " KB";
      setFiles([{ name: file.name, size: sizeKb }]);
      toast.success("File loaded, you can now analyze");
    };
    reader.readAsText(file);
  };

  const handleAnalyze = async (ddlStr: string) => {
    if (!ddlStr.trim()) {
      toast.error("Please provide a schema");
      return;
    }
    setLoading(true);
    try {
      const res = await parseSchema(ddlStr);
      setDdl(ddlStr);
      setParsedSchema(res.tables);
      setGenerationOrder(res.generation_order);
      setSchemaSummary(res.summary || "");
      toast.success("Schema analyzed successfully");
      navigate({ to: "/schema" });
    } catch (err: any) {
      toast.error(err.message || "Failed to analyze schema");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell
      title="Schema Upload"
      description="Upload a SQL schema or paste DDL. We'll parse tables, columns, types, and relationships."
    >
      <Tabs defaultValue="paste">
        <TabsList className="glass">
          <TabsTrigger value="paste">Paste SQL</TabsTrigger>
          <TabsTrigger value="drop">Drag &amp; Drop</TabsTrigger>
        </TabsList>

        <TabsContent value="drop" className="mt-4">
          <Card className="glass border-border/50">
            <CardContent className="p-6">
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  const file = e.dataTransfer.files[0];
                  if (file) {
                    handleFile(file);
                  }
                }}
                className={
                  "relative rounded-xl border-2 border-dashed transition-all p-12 text-center cursor-pointer " +
                  (dragging ? "border-primary bg-primary/5 scale-[1.01]" : "border-border bg-muted/30 hover:border-primary/50")
                }
              >
                <input
                  type="file"
                  accept=".sql,.ddl,.txt"
                  ref={fileInputRef}
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFile(file);
                    e.target.value = ''; // Reset to allow selecting the same file again
                  }}
                />
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl gradient-brand text-white shadow-glow mb-4">
                  <Upload className="h-7 w-7" />
                </div>
                <h3 className="font-display text-lg font-semibold">Click or drop your SQL files here</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Supports .sql, .ddl files up to 25MB · PostgreSQL, MySQL, SQL Server
                </p>
                <div className="mt-4 flex justify-center gap-2">
                  <Button
                    size="sm"
                    className="gradient-brand text-white border-0"
                    disabled={loading}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAnalyze(sql);
                    }}
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Upload & analyze"}
                  </Button>
                </div>
              </div>

              {files.length > 0 && (
                <div className="mt-6 space-y-2">
                  <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Queued files
                  </div>
                  {files.map((f, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-3 rounded-lg border border-border/60 bg-card/60 px-4 py-3"
                    >
                      <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                        <FileCode className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{f.name}</div>
                        <div className="text-xs text-muted-foreground">{f.size}</div>
                      </div>
                      <Badge
                        variant="outline"
                        className="border-emerald-500/30 bg-emerald-500/10 text-emerald-700 gap-1"
                      >
                        <CheckCircle2 className="h-3 w-3" /> Ready
                      </Badge>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => setFiles(files.filter((_, j) => j !== i))}
                      >
                        <X className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="paste" className="mt-4">
          <Card className="glass border-border/50">
            <CardHeader>
              <CardTitle className="text-base">Paste SQL schema</CardTitle>
              <CardDescription>Paste your CREATE TABLE statements below.</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={sql}
                onChange={(e) => setSql(e.target.value)}
                className="font-mono text-xs min-h-[320px] bg-background/60"
              />
              <div className="mt-4 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <FileText className="h-3.5 w-3.5" />
                  {sql.split("\n").length} lines · {sql.length} chars
                </div>
                <Button
                  className="gradient-brand text-white border-0"
                  disabled={loading}
                  onClick={() => handleAnalyze(sql)}
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null} Analyze
                  schema
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </AppShell>
  );
}
