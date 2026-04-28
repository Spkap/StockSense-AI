import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/ui/toast';
import { AuthProvider } from './context/AuthContext';
import { SidebarProvider } from './context/SidebarContext';
import { ThemeProvider } from './context/ThemeContext';
import ConvictionDeskApp from './features/conviction/ConvictionDeskApp';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <SidebarProvider>
            <ToastProvider>
              <ConvictionDeskApp />
            </ToastProvider>
          </SidebarProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
