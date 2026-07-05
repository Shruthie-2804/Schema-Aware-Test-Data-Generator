import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Upload,
  Database,
  Sparkles,
  ShieldCheck,
  TableProperties,
  Download,
  Boxes,
  Brain,
  Wand2,
  Eye,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
} from "@/components/ui/sidebar";

const mainItems = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Schema Upload", url: "/upload", icon: Upload },
  { title: "Schema Analysis", url: "/schema", icon: Database },
  { title: "Data Generator", url: "/generator", icon: Sparkles },
];

const qaItems = [
  { title: "Validation Center", url: "/validation", icon: ShieldCheck },
  { title: "Data Viewer", url: "/data", icon: TableProperties },
  { title: "Export Center", url: "/export", icon: Download },
];

const aiItems = [
  { title: "AI Schema Assistant", url: "/ai", icon: Brain },
  { title: "AI Recommendation", url: "/ai-recommend", icon: Wand2 },
  { title: "AI Schema Preview", url: "/ai-schema-preview", icon: Eye },
];

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const isActive = (url: string) =>
    url === "/" ? pathname === "/" : pathname.startsWith(url);

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2.5 px-2 py-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg gradient-brand shadow-glow">
            <Boxes className="h-5 w-5 text-white" />
          </div>
          <div className="flex flex-col leading-tight group-data-[collapsible=icon]:hidden">
            <span className="font-display text-sm font-semibold">TestDataGen</span>
            <span className="text-[10px] font-medium tracking-wider text-muted-foreground uppercase">
              AI · QA Platform
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainItems.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Quality Assurance</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {qaItems.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>AI Features</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {aiItems.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)} tooltip={item.title}>
                    <Link to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <div className="flex items-center gap-2 px-2 py-2 group-data-[collapsible=icon]:hidden">
          <div className="h-8 w-8 shrink-0 rounded-full gradient-brand flex items-center justify-center text-xs font-semibold text-white">
            AI
          </div>
          <div className="flex flex-col leading-tight min-w-0">
            <span className="text-xs font-medium truncate">AI-Powered Mode</span>
            <span className="text-[10px] text-muted-foreground truncate">Faker + Gemini/Groq/OpenAI</span>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
