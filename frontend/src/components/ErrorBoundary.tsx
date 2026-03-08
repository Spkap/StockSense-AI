import { Component, ErrorInfo, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import { Button } from './ui/button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('Uncaught error:', error, errorInfo);
  }

  handleRefresh = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-canvas p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md"
          >
            <div className="border border-kill/30 bg-surface-1 rounded-sm overflow-hidden">
              <div className="h-[2px] w-full bg-kill" />
              <div className="flex flex-col items-center p-8 text-center">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-sm bg-kill/10 border border-kill/20">
                   <AlertCircle className="h-8 w-8 text-kill" />
                </div>
                
                <h2 className="mb-2 text-lg font-mono font-bold tracking-widest uppercase text-txt-primary">
                  FATAL_ERROR
                </h2>
                
                <p className="mb-6 text-micro font-mono text-txt-muted uppercase tracking-widest">
                  An unexpected error occurred. Please refresh.
                </p>
                
                <div className="mb-8 w-full rounded-sm bg-canvas p-4 border border-kill/20">
                  <p className="font-mono text-micro text-kill break-all uppercase tracking-wider">
                    {this.state.error?.message || 'Unknown error'}
                  </p>
                </div>
                
                <Button 
                  onClick={this.handleRefresh} 
                  className="w-full font-mono text-micro uppercase tracking-widest border border-kill bg-kill/10 text-kill hover:bg-kill/20 rounded-sm h-9"
                >
                  [REFRESH_PAGE]
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
