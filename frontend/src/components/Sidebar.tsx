import { useRef, useEffect } from 'react';
import { 
  LayoutDashboard, 
  LineChart, 
  BookOpen,
  Bell,
  ChevronLeft,
  X,
} from 'lucide-react';
import { cn } from '../utils/cn';
import { useSidebar } from '../context/SidebarContext';
import { Button } from './ui/button';

type ViewType = 'dashboard' | 'theses' | 'alerts';

const menuItems: Array<{
  icon: typeof LayoutDashboard;
  label: string;
  viewId: ViewType;
  implemented: boolean;
}> = [
  { icon: LayoutDashboard, label: 'Dashboard', viewId: 'dashboard', implemented: true },
  { icon: BookOpen, label: 'My Theses', viewId: 'theses', implemented: true },
  { icon: Bell, label: 'Alerts', viewId: 'alerts', implemented: true },
];

interface SidebarContentProps {
  isCollapsed: boolean;
  isMobile?: boolean;
  onClose?: () => void;
  tabIndex?: number;
  currentView: ViewType;
  onNavigate: (view: ViewType) => void;
}

const SidebarContent = ({ isCollapsed, isMobile, onClose, tabIndex = 0, currentView, onNavigate }: SidebarContentProps) => {
  return (
    <div className="flex h-full flex-col">
      {/* Brand */}
      <div className={cn(
        "flex items-center gap-3 px-3 py-6",
        isCollapsed && !isMobile && "justify-center px-0"
      )}>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
          <LineChart className="h-6 w-6" />
        </div>
        {(!isCollapsed || isMobile) && (
          <span className="text-xl font-bold tracking-tight text-foreground">
            StockSense
          </span>
        )}
        {isMobile && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="ml-auto"
            aria-label="Close menu"
            tabIndex={tabIndex}
          >
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>

      {/* Main Menu */}
      <nav className="flex-1 space-y-2 px-2 mt-4">
        {menuItems.map((item) => (
          <button
            key={item.label}
            tabIndex={item.implemented ? tabIndex : -1}
            disabled={!item.implemented}
            onClick={() => {
              onNavigate(item.viewId);
              if (isMobile && onClose) onClose();
            }}
            className={cn(
              "group flex w-full items-center gap-3 rounded-xl px-3 py-3 text-[15px] font-medium transition-all duration-200",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              currentView === item.viewId
                ? "bg-primary text-primary-foreground shadow-md"
                : item.implemented
                  ? "text-muted-foreground hover:bg-muted hover:text-foreground"
                  : "text-muted-foreground/40 cursor-not-allowed",
              isCollapsed && !isMobile && "justify-center px-2"
            )}
            title={!item.implemented ? `${item.label} — Coming Soon` : (isCollapsed && !isMobile ? item.label : undefined)}
          >
            <item.icon className={cn("h-5 w-5 shrink-0 transition-transform duration-200", !item.implemented && "opacity-50", currentView === item.viewId && "scale-110")} />
            {(!isCollapsed || isMobile) && (
              <span className="flex items-center gap-2">
                {item.label}
                {!item.implemented && <span className="text-[10px] uppercase tracking-wider opacity-60">Soon</span>}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom Section (optional footer area) */}
      <div className="mt-auto px-4 py-6">
          {(!isCollapsed || isMobile) && (
            <p className="text-xs text-muted-foreground text-center">
               v0.2.0 Beta
            </p>
          )}
      </div>
    </div>
  );
};

interface SidebarProps {
  onNavigate: (view: ViewType) => void;
  currentView: ViewType;
}

const Sidebar = ({ onNavigate, currentView }: SidebarProps) => {
  const { isCollapsed, isMobileOpen, toggleCollapsed, closeMobile } = useSidebar();
  const mobileDrawerRef = useRef<HTMLDivElement>(null);
  const hamburgerButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (isMobileOpen) {
      hamburgerButtonRef.current = document.querySelector('[aria-label="Open menu"]');
    }
  }, [isMobileOpen]);

  useEffect(() => {
    if (isMobileOpen && mobileDrawerRef.current) {
      const drawer = mobileDrawerRef.current;
      const focusableElements = drawer.querySelectorAll<HTMLElement>(
        'button:not([tabindex="-1"]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0];
      setTimeout(() => firstElement?.focus(), 100);

      const handleTabKey = (e: KeyboardEvent) => {
        if (e.key !== 'Tab') return;
        const lastElement = focusableElements[focusableElements.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      };
      drawer.addEventListener('keydown', handleTabKey);
      return () => drawer.removeEventListener('keydown', handleTabKey);
    } else if (!isMobileOpen && hamburgerButtonRef.current) {
      hamburgerButtonRef.current.focus();
    }
  }, [isMobileOpen]);

  return (
    <>
      <aside 
        className={cn(
          "fixed left-0 top-0 z-40 hidden h-screen flex-col border-r border-border bg-card transition-all duration-300 ease-in-out md:flex",
          isCollapsed ? "w-20" : "w-72"
        )}
      >
        <SidebarContent isCollapsed={isCollapsed} currentView={currentView} onNavigate={onNavigate} />
        
        <Button
          variant="outline"
          size="icon"
          onClick={toggleCollapsed}
          className="absolute -right-3 top-24 h-6 w-6 rounded-full border-border bg-card shadow-sm hover:shadow-md transition-shadow"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className={cn(
            "h-3 w-3 transition-transform duration-300",
            isCollapsed && "rotate-180"
          )} />
        </Button>
      </aside>

      {isMobileOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      <aside
        ref={mobileDrawerRef}
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-border bg-card shadow-2xl transition-transform duration-300 ease-out md:hidden",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-hidden={!isMobileOpen}
      >
        <SidebarContent 
          isCollapsed={false} 
          isMobile 
          onClose={closeMobile}
          tabIndex={isMobileOpen ? 0 : -1}
          currentView={currentView}
          onNavigate={onNavigate}
        />
      </aside>
    </>
  );
};

export default Sidebar;
