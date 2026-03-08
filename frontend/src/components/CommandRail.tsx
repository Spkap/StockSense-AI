import { LayoutDashboard, BookOpen, Bell, Box } from 'lucide-react';
import { cn } from '../utils/cn';

type ViewType = 'dashboard' | 'theses' | 'alerts';

interface CommandRailProps {
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
}

const menuItems: Array<{
  icon: typeof LayoutDashboard;
  label: string;
  viewId: ViewType;
}> = [
  { icon: LayoutDashboard, label: 'ANALYSIS', viewId: 'dashboard' },
  { icon: BookOpen, label: 'THESES', viewId: 'theses' },
  { icon: Bell, label: 'SYS_ALERTS', viewId: 'alerts' },
];

export default function CommandRail({ currentView, onNavigate }: CommandRailProps) {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-14 flex-col items-center border-r border-border-base bg-surface-1 py-0">
      {/* Brand Icon */}
      <div className="flex h-14 w-full items-center justify-center text-txt-primary border-b border-border-base bg-surface-2/30 relative">
        <Box className="h-5 w-5" />
        <div className="absolute bottom-0 h-[1px] w-full bg-accent/20" />
      </div>

      {/* Navigation Nodes */}
      <nav className="flex flex-1 flex-col items-center w-full mt-4 gap-1">
        {menuItems.map((item) => {
          const isActive = currentView === item.viewId;
          return (
            <button
              key={item.label}
              onClick={() => onNavigate(item.viewId)}
              className={cn(
                "group relative flex h-12 w-full items-center justify-center transition-colors outline-none",
                isActive 
                  ? "border-l-[3px] border-accent bg-surface-2 text-accent" 
                  : "border-l-[3px] border-transparent text-txt-muted hover:text-txt-primary hover:bg-surface-2 hover:border-border-strong"
              )}
              aria-label={item.label}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              
              {/* Tooltip */}
              <div className="absolute left-14 hidden items-center border border-border-base bg-surface-1 px-3 py-1.5 text-micro uppercase font-mono tracking-widest text-txt-primary group-hover:flex whitespace-nowrap z-50 rounded-sm font-bold">
                {item.label}
              </div>
            </button>
          );
        })}
      </nav>

      {/* Bottom Profile / Settings Area */}
      <div className="mt-auto flex h-14 w-full items-center justify-center border-t border-border-base bg-surface-2/10 text-txt-muted hover:text-txt-primary hover:bg-surface-2 cursor-pointer transition-colors outline-none">
        <span className="text-micro font-mono font-bold tracking-widest uppercase writing-vertical">USR_SK</span>
      </div>
    </aside>
  );
}
