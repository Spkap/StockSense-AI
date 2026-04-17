import { useState } from 'react';
import { Menu } from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';
import AuthModal from './AuthModal';
import { useSidebar } from '../context/SidebarContext';
import { VIEW_META, type AppView } from '../types/navigation';

interface HeaderProps {
  currentView: AppView;
  onNavigate: (view: AppView) => void;
}

const Header = ({ currentView, onNavigate }: HeaderProps) => {
  const { toggleMobile } = useSidebar();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const meta = VIEW_META[currentView];

  return (
    <>
      <header className="sticky top-0 z-30 flex h-20 items-center justify-between px-6 transition-all duration-300 md:px-10 bg-background/60 backdrop-blur-xl border-b border-border/40 supports-[backdrop-filter]:bg-background/60">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMobile}
            className="md:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* Minimalist Title / Breadcrumbs */}
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground/90">
              {meta.title}
            </h1>
            <p className="hidden text-sm font-medium text-muted-foreground/60 md:block">
              {meta.subtitle}
            </p>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3 bg-secondary/30 backdrop-blur-md p-1.5 rounded-full border border-white/10 shadow-sm dark:border-white/5">
          <ThemeToggle />
          <UserMenu onOpenAuth={() => setShowAuthModal(true)} onNavigate={onNavigate} />
        </div>
      </header>

      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
      />
    </>
  );
};

export default Header;
