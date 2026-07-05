import type { ReactNode } from "react";
import { useEffect } from "react";
import { Bell, Search, Sparkles, HelpCircle, Wifi, WifiOff } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useStore } from "@/lib/store";
import { checkHealth } from "@/lib/api";

interface AppShellProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}

/** Polls the backend health endpoint every 30 s and updates the global store. */
function useBackendHealth() {
  const setBackendStatus = useStore((s) => s.setBackendStatus);

  useEffect(() => {
    let cancelled = false;

    async function ping() {
      try {
        await checkHealth();
        if (!cancelled) setBackendStatus("connected");
      } catch {
        if (!cancelled) setBackendStatus("disconnected");
      }
    }

    ping();
    const id = setInterval(ping, 30_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [setBackendStatus]);
}

export function AppShell({ title, description, actions, children }: AppShellProps) {
  useBackendHealth();
  const backendStatus = useStore((s) => s.backendStatus);

  const statusColor =
    backendStatus === "connected"
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
      : backendStatus === "disconnected"
        ? "border-red-500/40 bg-red-500/10 text-red-700"
        : "border-amber-500/40 bg-amber-500/10 text-amber-700";

  const StatusIcon = backendStatus === "connected" ? Wifi : WifiOff;
  const statusLabel =
    backendStatus === "connected"
      ? "Backend connected"
      : backendStatus === "disconnected"
        ? "Backend offline"
        : "Connecting…";

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border/60 glass-strong px-4 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="h-6" />
        <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
          <span>TestDataGen</span>
          <span className="opacity-40">/</span>
          <span className="text-foreground font-medium">{title}</span>
        </div>

        <div className="ml-auto flex items-center gap-2">
          {/* Backend connection status badge */}
          <Badge
            variant="outline"
            className={`hidden sm:inline-flex items-center gap-1.5 h-7 ${statusColor} transition-colors`}
          >
            <StatusIcon className="h-3 w-3" />
            {statusLabel}
          </Badge>

          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search tables, schemas, runs…"
              className="h-9 w-64 pl-9 bg-background/60"
            />
            <kbd className="absolute right-2 top-1/2 -translate-y-1/2 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
              ⌘K
            </kbd>
          </div>
          <Button variant="ghost" size="icon" className="h-9 w-9">
            <HelpCircle className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-9 w-9 relative">
            <Bell className="h-4 w-4" />
            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-destructive" />
          </Button>
          <Badge
            variant="outline"
            className="hidden lg:inline-flex gap-1.5 h-7 border-primary/30 bg-primary/5 text-primary"
          >
            <Sparkles className="h-3 w-3" />
            Pro
          </Badge>
        </div>
      </header>

      <div className="flex-1 px-4 py-6 lg:px-8 lg:py-8 animate-float-in">
        <div className="mx-auto max-w-[1400px] space-y-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="font-display text-2xl lg:text-3xl font-semibold tracking-tight">
                {title}
              </h1>
              {description && (
                <p className="mt-1 text-sm text-muted-foreground max-w-2xl">{description}</p>
              )}
            </div>
            {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
