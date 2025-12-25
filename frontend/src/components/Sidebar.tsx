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

// Secondary items removed - none are implemented

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
    <>
      {/* Brand */}
      <div className={cn(
        "mb-8 flex items-center gap-2 px-2",
        isCollapsed && !isMobile && "justify-center px-0"
      )}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <LineChart className="h-5 w-5" />
        </div>
        {(!isCollapsed || isMobile) && (
          <span className="text-lg font-bold tracking-tight text-foreground">
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
      <nav className="flex-1 space-y-1">
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
              "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              currentView === item.viewId
                ? "bg-primary text-primary-foreground shadow-sm"
                : item.implemented
                  ? "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  : "text-muted-foreground/40 cursor-not-allowed",
              isCollapsed && !isMobile && "justify-center px-2"
            )}
            title={!item.implemented ? `${item.label} — Coming Soon` : (isCollapsed && !isMobile ? item.label : undefined)}
          >
            <item.icon className={cn("h-4 w-4 shrink-0", !item.implemented && "opacity-50")} />
            {(!isCollapsed || isMobile) && (
              <span className="flex items-center gap-2">
                {item.label}
                {!item.implemented && <span className="text-[10px] uppercase tracking-wider opacity-60">Soon</span>}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* User Profile - will integrate with AuthContext */}
    </>
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

  // Store reference to button that opened the drawer
  useEffect(() => {
    if (isMobileOpen) {
      // Find and store the hamburger button when drawer opens
      hamburgerButtonRef.current = document.querySelector('[aria-label="Open menu"]');
    }
  }, [isMobileOpen]);

  // Focus trap for mobile drawer
  useEffect(() => {
    if (isMobileOpen && mobileDrawerRef.current) {
      const drawer = mobileDrawerRef.current;
      
      // Focus the first focusable element when drawer opens
      const focusableElements = drawer.querySelectorAll<HTMLElement>(
        'button:not([tabindex="-1"]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0];
      
      // Delay focus to allow transition
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
      // Return focus to hamburger button when drawer closes
      hamburgerButtonRef.current.focus();
    }
  }, [isMobileOpen]);

  return (
    <>
      {/* Desktop Sidebar */}
      <aside 
        className={cn(
          "fixed left-0 top-0 z-40 hidden h-screen flex-col border-r border-border bg-card p-4 transition-all duration-300 ease-in-out md:flex",
          isCollapsed ? "w-16" : "w-64"
        )}
      >
        <SidebarContent isCollapsed={isCollapsed} currentView={currentView} onNavigate={onNavigate} />
        
        {/* Collapse Toggle Button */}
        <Button
          variant="outline"
          size="icon"
          onClick={toggleCollapsed}
          className="absolute -right-3 top-20 h-6 w-6 rounded-full border-border bg-card shadow-md"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className={cn(
            "h-3 w-3 transition-transform duration-300",
            isCollapsed && "rotate-180"
          )} />
        </Button>
      </aside>

      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer */}
      <aside
        ref={mobileDrawerRef}
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-border bg-card p-4 transition-transform duration-300 ease-in-out md:hidden",
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
