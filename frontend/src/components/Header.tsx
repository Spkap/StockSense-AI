import { useState } from 'react';
import UserMenu from './UserMenu';
import AuthModal from './AuthModal';

const Header = () => {
  const [showAuthModal, setShowAuthModal] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between px-6 md:px-8 bg-canvas border-b border-border-base">
        {/* Left Section - Minimalist */}
        <div className="flex items-center gap-4 text-txt-primary">
          <span className="text-sm font-mono font-bold tracking-widest text-txt-primary">
            STOCKSENSE_SYS_V2.0
          </span>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
          <UserMenu onOpenAuth={() => setShowAuthModal(true)} />
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
