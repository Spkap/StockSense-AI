import { Activity, Bell, BookOpen, LogOut, PanelLeft, Search, ShieldCheck } from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { Button } from '../../components/ui/button';
import ThemeToggle from '../../components/ThemeToggle';
import { cn } from '../../utils/cn';
import type { ConvictionView } from './types';

interface DeskShellProps {
  view: ConvictionView;
  onViewChange: (view: ConvictionView) => void;
  backendStatus: 'online' | 'offline' | 'checking';
  userEmail?: string | null;
  onSignIn: () => void;
  onSignOut: () => void;
  children: ReactNode;
}

const navItems: Array<{ id: ConvictionView; label: string; description: string; icon: typeof BookOpen }> = [
  { id: 'workbench', label: 'Thesis Desk', description: 'Memory and conviction checks', icon: BookOpen },
  { id: 'research', label: 'Research Intake', description: 'Turn ticker research into a thesis', icon: Search },
  { id: 'alerts', label: 'Alerts', description: 'Kill criteria and action queue', icon: Bell },
];

function SystemStatusFloat({ status }: { status: DeskShellProps['backendStatus'] }) {
  return (
    <div className="fixed bottom-3 right-6 z-50 md:bottom-3 md:right-8 group cursor-default flex items-center h-6">
      <div className="relative flex size-1.5 items-center justify-center shrink-0">
        {status === 'online' && <span className="absolute size-full animate-ping rounded-full bg-success/50" style={{ animationDuration: '2s' }}></span>}
        {status === 'checking' && <span className="absolute size-full animate-ping rounded-full bg-muted-foreground/50" style={{ animationDuration: '2s' }}></span>}
        <span
          className={cn(
            'relative size-1.5 rounded-full',
            status === 'online' ? 'bg-success/80' : status === 'offline' ? 'bg-destructive/80' : 'bg-muted-foreground/80'
          )}
        />
      </div>
      
      <div className="grid transition-all duration-500 ease-out grid-cols-[0fr] group-hover:grid-cols-[1fr]">
        <div className="overflow-hidden">
          <span className={cn(
            "whitespace-nowrap pl-2 text-[10px] uppercase tracking-wider font-semibold opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75",
            status === 'online' ? 'text-success/70' : status === 'offline' ? 'text-destructive/70' : 'text-muted-foreground/70'
          )}>
            {status === 'online' ? 'Connected' : status === 'offline' ? 'Disconnected' : 'Checking'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function DeskShell({
  view,
  onViewChange,
  backendStatus,
  userEmail,
  onSignIn,
  onSignOut,
  children,
}: DeskShellProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <div className={cn(
        "min-h-[100dvh] transition-[grid-template-columns] duration-300 ease-in-out md:grid",
        isSidebarOpen ? "md:grid-cols-[280px_minmax(0,1fr)]" : "md:grid-cols-[72px_minmax(0,1fr)]"
      )}>
        <aside className="flex flex-col border-b border-border/40 bg-card/40 px-4 py-3 backdrop-blur-xl md:border-b-0 md:border-r md:px-0 md:py-4 md:sticky md:top-0 md:h-[100dvh] overflow-y-auto">
          <div className="flex items-center justify-between gap-3 px-4 md:block">
            <div className={cn("flex items-center gap-3", !isSidebarOpen && "md:justify-center md:gap-0")}>
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-lux dark:shadow-lux-dark">
                <ShieldCheck className="size-5" />
              </div>
              <div className={cn("transition-all duration-300 md:block", !isSidebarOpen && "md:hidden md:opacity-0 md:w-0")}>
                <div className="text-sm font-semibold tracking-tight whitespace-nowrap">StockSense</div>
                <div className="text-xs text-muted-foreground whitespace-nowrap">Conviction Desk</div>
              </div>
            </div>
          </div>

          <nav className="mt-4 grid grid-cols-3 gap-2 px-2 md:mt-8 md:grid-cols-1 md:gap-1.5 md:px-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = view === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onViewChange(item.id)}
                  title={!isSidebarOpen ? item.label : undefined}
                  className={cn(
                    'flex min-h-14 items-center gap-3 rounded-xl px-2 py-2 transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:min-h-10 md:py-2',
                    isSidebarOpen 
                      ? 'justify-center md:justify-start md:px-3' 
                      : 'justify-center md:px-0 md:w-12 md:mx-auto',
                    active
                      ? 'bg-primary text-primary-foreground shadow-lux dark:shadow-lux-dark ring-1 ring-primary/10'
                      : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground'
                  )}
                >
                  <Icon className="size-5 shrink-0" />
                  <span className={cn("grid gap-0.5 text-left transition-all duration-300", !isSidebarOpen && "md:hidden md:opacity-0 md:w-0")}>
                    <span className="text-xs font-medium leading-tight md:text-sm whitespace-nowrap">{item.label}</span>
                  </span>
                </button>
              );
            })}
          </nav>

        </aside>

        <main className="min-w-0">
          <header className="sticky top-0 z-20 border-b border-border/40 bg-background/80 px-4 py-4 backdrop-blur-xl md:px-8">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <Button 
                  variant="ghost" 
                  size="icon" 
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
                  className="hidden md:flex h-9 w-9 text-muted-foreground hover:text-foreground"
                  title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                >
                  <PanelLeft className="size-5" />
                </Button>
                <div>
                  <h1 className="text-xl font-semibold tracking-tight md:text-2xl">
                  {view === 'workbench' ? 'Thesis Desk' : view === 'research' ? 'Research Intake' : 'Alerts'}
                </h1>
                  <p className="text-sm text-muted-foreground">
                    {view === 'workbench'
                      ? 'Review thesis memory, run conviction checks, and inspect evidence.'
                      : view === 'research'
                        ? 'Use fresh ticker research to create or update a thesis.'
                        : 'Review kill criteria and act on thesis drift.'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <ThemeToggle />
                {userEmail ? (
                  <>
                    <div className="hidden max-w-[220px] truncate text-sm text-muted-foreground sm:block">{userEmail}</div>
                    <Button variant="outline" size="sm" onClick={onSignOut}>
                      <LogOut className="size-4" />
                      Sign out
                    </Button>
                  </>
                ) : (
                  <Button size="sm" onClick={onSignIn}>
                    Sign in
                  </Button>
                )}
              </div>
            </div>
          </header>

          <div className="px-4 py-5 md:px-8 md:py-7">{children}</div>
        </main>
      </div>
      
      <SystemStatusFloat status={backendStatus} />
    </div>
  );
}
