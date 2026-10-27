import { useState } from 'react';
import UserMenu from './UserMenu';
import AuthModal from './AuthModal';
import { useHealthCheck } from '../api/hooks';

const Header = () => {
  const { data: health, isError } = useHealthCheck();
  const status = isError ? 'Offline' : health?.status === 'ok' ? 'Connected' : health?.status === 'degraded' ? 'Limited data' : 'Connecting';
  const [showAuthModal, setShowAuthModal] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-30 flex min-h-14 flex-wrap gap-2 items-center justify-between px-3 py-2 md:px-8 bg-canvas border-b border-border-base">
        {/* Left Section - Minimalist */}
        <div className="flex items-center gap-4 text-txt-primary">
          <span className="text-sm font-mono font-bold tracking-widest text-txt-primary">
            <span className="sm:hidden">StockSense</span><span className="hidden sm:inline">STOCKSENSE_SYS_V2.0</span>
          </span>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <span role="status" aria-label={`Service: ${status}`} title={`Service: ${status}`} className="flex items-center gap-2 text-micro font-mono text-txt-muted">
            <span className={`h-1.5 w-1.5 rounded-full ${status === 'Connected' ? 'bg-bull' : status === 'Offline' ? 'bg-bear' : 'bg-accent'}`} />
            <span className="hidden lg:inline">{status}</span>
          </span>
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
