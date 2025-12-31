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
      <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-border bg-background/95 px-6 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:px-10">
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
            <Menu className="h-6 w-6" />
          </Button>

          {/* Breadcrumbs / Page Title */}
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Dashboard
            </h1>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
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
