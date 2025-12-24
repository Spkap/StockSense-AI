import { useState } from 'react';
import { 
  ChevronRight,
  Menu,
} from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';
import AuthModal from './AuthModal';
import { useSidebar } from '../context/SidebarContext';

const Header = () => {
  const { toggleMobile } = useSidebar();
  const [showAuthModal, setShowAuthModal] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:px-8">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {/* Mobile Hamburger */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMobile}
            className="md:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* Breadcrumbs / Page Title */}
          <div>
            <h1 className="text-lg font-bold tracking-tight text-foreground md:text-xl">
              Dashboard
            </h1>
            <div className="hidden items-center gap-1 text-xs text-muted-foreground md:flex">
              <span className="hover:text-foreground cursor-pointer transition-colors">Home</span>
              <ChevronRight className="h-3 w-3" />
              <span className="font-medium text-foreground">Dashboard</span>
            </div>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2 md:gap-4">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Menu */}
          <UserMenu onOpenAuth={() => setShowAuthModal(true)} />
        </div>
      </header>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={showAuthModal} 
        onClose={() => setShowAuthModal(false)} 
      />
    </>
  );
};

export default Header;

