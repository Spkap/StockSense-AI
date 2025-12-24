import { Component, ErrorInfo, ReactNode } from 'react';
import { motion } from 'framer-motion';
import { AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

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
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full max-w-md"
          >
            <Card className="border-destructive/20 bg-destructive/5 shadow-2xl overflow-hidden">
               <div className="absolute top-0 w-full h-1 bg-gradient-to-r from-destructive/50 to-destructive" />
              <CardContent className="flex flex-col items-center p-8 text-center">
                <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10">
                   <AlertCircle className="h-10 w-10 text-destructive" />
                </div>
                
                <h2 className="mb-2 text-2xl font-bold tracking-tight text-foreground">
                  Something went wrong
                </h2>
                
                <p className="mb-6 text-muted-foreground">
                  An unexpected error occurred. Please try refreshing the page.
                </p>
                
                <div className="mb-8 w-full rounded-md bg-background/50 p-4 border border-destructive/20">
                  <p className="font-mono text-xs text-destructive break-all">
                    {this.state.error?.message || 'Unknown error'}
                  </p>
                </div>
                
                <Button onClick={this.handleRefresh} variant="destructive" className="w-full">
                  Refresh Page
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
