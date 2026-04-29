import { Activity, Bell, BookOpen, Clock3, CloudOff, LogOut, PanelLeft, Search, ShieldCheck } from 'lucide-react';
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
  { id: 'workbench', label: 'Thesis Desk', description: 'Saved beliefs and checks', icon: BookOpen },
  { id: 'research', label: 'Research Room', description: 'Evidence-first investigation', icon: Search },
  { id: 'alerts', label: 'Alerts', description: 'Kill criteria and drift', icon: Bell },
];

const viewCopy: Record<ConvictionView, { title: string; description: string }> = {
  workbench: {
    title: 'Thesis Desk',
    description: 'Saved beliefs, fresh evidence, and every reason to change your mind.',
  },
  research: {
    title: 'Research Room',
    description: 'Run an evidence-first investigation before a narrative becomes thesis memory.',
  },
  alerts: {
    title: 'Alerts',
    description: 'Kill criteria, thesis drift, and the decisions that need attention.',
  },
};

function BackendStatusBadge({ status, className }: { status: DeskShellProps['backendStatus']; className?: string }) {
  const meta =
    status === 'online'
      ? {
          label: 'Data API online',
          detail: 'Runs and receipts can stream',
          icon: Activity,
          className: 'border-success/25 bg-success/10 text-success',
        }
      : status === 'checking'
        ? {
            label: 'Checking API',
            detail: 'Waiting for health response',
            icon: Clock3,
            className: 'border-border bg-secondary text-muted-foreground',
          }
        : {
            label: 'Data API offline',
            detail: 'Start the backend before running checks',
            icon: CloudOff,
            className: 'border-destructive/25 bg-destructive/10 text-destructive',
          };
  const Icon = meta.icon;

  return (
    <div className={cn('flex w-fit items-center gap-2 rounded-lg border px-3 py-2 text-xs', meta.className, className)} title={meta.detail}>
      <Icon className="size-3.5" />
      <span className="font-medium">{meta.label}</span>
    </div>
  );
}

function SystemStatusFloat({ status }: { status: DeskShellProps['backendStatus'] }) {
  return (
    <div className="fixed bottom-3 right-6 z-50 hidden h-6 cursor-default items-center md:bottom-3 md:right-8 md:flex group">
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
  const activeView = viewCopy[view];

  return (
    <div className="desk-shell-bg min-h-[100dvh] bg-background text-foreground">
      <div className={cn(
        "min-h-[100dvh] transition-[grid-template-columns] duration-300 ease-in-out md:grid",
        isSidebarOpen ? "md:grid-cols-[280px_minmax(0,1fr)]" : "md:grid-cols-[72px_minmax(0,1fr)]"
      )}>
        <aside className="flex flex-col border-b border-border/50 bg-card/75 px-4 py-3 shadow-sm backdrop-blur-xl md:sticky md:top-0 md:h-[100dvh] md:border-b-0 md:border-r md:px-0 md:py-4 overflow-y-auto">
          <div className="flex items-center justify-between gap-3 px-4 md:block">
            <div className={cn("flex items-center gap-3", !isSidebarOpen && "md:justify-center md:gap-0")}>
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-lux dark:shadow-lux-dark">
                <ShieldCheck className="size-5" />
              </div>
              <div className={cn("transition-all duration-300 md:block", !isSidebarOpen && "md:hidden md:opacity-0 md:w-0")}>
                <div className="text-sm font-semibold tracking-tight whitespace-nowrap">Conviction Desk</div>
                <div className="text-xs text-muted-foreground whitespace-nowrap">StockSense research OS</div>
              </div>
            </div>
          </div>

          <nav className="mt-4 grid grid-cols-3 gap-2 px-0 md:mt-8 md:grid-cols-1 md:gap-1.5 md:px-3">
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
                    'flex min-h-14 min-w-0 items-center rounded-lg px-1.5 py-2 transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:min-h-11 md:gap-3 md:py-2',
                    isSidebarOpen 
                      ? 'flex-col justify-center gap-1 md:flex-row md:justify-start md:px-3'
                      : 'justify-center md:px-0 md:w-12 md:mx-auto',
                    active
                      ? 'bg-primary text-primary-foreground shadow-lux dark:shadow-lux-dark ring-1 ring-primary/10'
                      : 'text-muted-foreground hover:bg-secondary/70 hover:text-foreground'
                  )}
                >
                  <Icon className="size-5 shrink-0" />
                  <span className={cn("grid min-w-0 gap-0.5 text-center transition-all duration-300 md:text-left", !isSidebarOpen && "md:hidden md:opacity-0 md:w-0")}>
                    <span className="max-w-full truncate text-[11px] font-medium leading-tight md:text-sm md:whitespace-nowrap max-[360px]:sr-only">{item.label}</span>
                    <span className="hidden text-[11px] leading-tight text-current/65 md:block">{item.description}</span>
                  </span>
                </button>
              );
            })}
          </nav>

        </aside>

        <main className="min-w-0">
          <header className="sticky top-0 z-20 border-b border-border/50 bg-background/80 px-4 py-4 backdrop-blur-xl md:px-8">
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
                    {activeView.title}
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    {activeView.description}
                  </p>
                  <BackendStatusBadge status={backendStatus} className="mt-2 md:hidden" />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <BackendStatusBadge status={backendStatus} className="hidden md:flex" />
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
