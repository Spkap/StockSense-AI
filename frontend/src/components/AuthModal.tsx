/**
 * Auth Modal - Login/Signup UI
 * Stage 3: User Belief System
 * Styled for Obsidian Terminal aesthetic (sharp, mono, dense)
 */

import { useState } from 'react';
import { LogIn, Mail, Lock, Loader2, X, Terminal } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { signInWithGoogle, signInWithEmail, signUpWithEmail } = useAuth();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = mode === 'login' 
        ? await signInWithEmail(email, password)
        : await signUpWithEmail(email, password);

      if (result.error) {
        setError(result.error.message);
      } else {
        onClose();
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (err) {
      setError('Failed to sign in with Google');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-md border border-border-base bg-canvas shadow-none rounded-sm overflow-hidden flex flex-col relative">
        
        {/* Terminal-like Header */}
        <div className="flex items-center justify-between border-b border-border-base bg-surface-1 px-4 py-3">
            <div className="flex items-center gap-2 text-txt-muted">
                <Terminal className="h-4 w-4" />
                <span className="text-micro uppercase font-mono tracking-widest leading-none">
                    {mode === 'login' ? 'AUTH_SYS // LOGIN' : 'AUTH_SYS // REGISTER'}
                </span>
            </div>
            <button 
                onClick={onClose}
                className="p-1 hover:bg-surface-2 hover:text-kill text-txt-muted transition-colors rounded-sm outline-none"
            >
                <X className="h-4 w-4" />
            </button>
        </div>

        <div className="p-6 md:p-8 space-y-6">
          <div className="flex flex-col gap-1 text-center mb-6">
            <h2 className="text-xl font-mono font-bold text-txt-primary uppercase tracking-tight">
              {mode === 'login' ? 'ESTABLISH_CONNECTION' : 'INITIALIZE_USER'}
            </h2>
            <p className="text-micro font-mono uppercase tracking-widest text-txt-muted">
              {mode === 'login' 
                ? 'Authenticate to access knowledge base' 
                : 'Configure new analyst credentials'}
            </p>
          </div>
          
          <div className="space-y-6">
            {/* Google Sign In */}
            <Button
              variant="outline"
              className="w-full h-10 gap-3 rounded-sm border-border-base bg-surface-1 hover:bg-surface-2 hover:text-txt-primary border font-mono text-sm uppercase tracking-widest text-txt-secondary"
              onClick={handleGoogleSignIn}
              disabled={loading}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              AUTH_VIA_GOOGLE
            </Button>

            <div className="relative flex items-center justify-center">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border-base/50" />
              </div>
              <div className="relative flex justify-center text-micro font-mono tracking-widest uppercase">
                <span className="bg-canvas px-3 text-txt-muted">OR_MANUAL_ENTRY</span>
              </div>
            </div>

            {/* Email Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-micro font-mono uppercase tracking-widest text-txt-secondary flex items-center gap-2">
                    <Mail className="h-3 w-3" />
                    USER_IDENTIFIER
                </label>
                <div className="relative">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="analyst@domain.com"
                    required
                    className="w-full h-10 px-3 rounded-sm border border-border-base bg-surface-1 text-txt-primary font-mono text-sm placeholder:text-txt-muted/50 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-micro font-mono uppercase tracking-widest text-txt-secondary flex items-center gap-2">
                    <Lock className="h-3 w-3" />
                    SECURITY_KEY
                </label>
                <div className="relative">
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    minLength={6}
                    className="w-full h-10 px-3 rounded-sm border border-border-base bg-surface-1 text-txt-primary font-mono text-sm placeholder:text-txt-muted/50 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
                  />
                </div>
              </div>

              {error && (
                <div className="p-2 border border-kill/30 bg-kill/10 rounded-sm">
                    <p className="text-micro font-mono text-kill uppercase tracking-widest text-center">ERR: {error}</p>
                </div>
              )}

              <Button
                type="submit"
                className="w-full h-10 rounded-sm bg-accent text-canvas hover:bg-accent/90 focus:ring-offset-canvas font-mono text-sm uppercase tracking-widest flex items-center gap-2 mt-4"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-canvas" />
                    EXECUTING...
                  </>
                ) : (
                  <>
                    <LogIn className="h-4 w-4" />
                    {mode === 'login' ? 'EXECUTE_LOGIN' : 'EXECUTE_REGISTER'}
                  </>
                )}
              </Button>
            </form>

            {/* Toggle Mode */}
            <div className="flex justify-center pt-2">
                <button
                type="button"
                onClick={() => {
                    setMode(mode === 'login' ? 'signup' : 'login');
                    setError(null);
                }}
                className="text-micro font-mono tracking-widest text-txt-muted hover:text-accent uppercase transition-colors"
                >
                {mode === 'login' ? '>> REQUEST_NEW_CREDENTIALS' : '>> USE_EXISTING_CREDENTIALS'}
                </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
