import { useState } from 'react';
import AuthModal from '../../components/AuthModal';
import { useHealthCheck } from '../../api/hooks';
import { useAuth } from '../../context/AuthContext';
import type { ConvictionView } from './types';
import AlertsQueue from './AlertsQueue';
import DeskShell from './DeskShell';
import ResearchRoom from './ResearchRoom';
import ThesisWorkbench from './ThesisWorkbench';

export default function ConvictionDeskApp() {
  const [view, setView] = useState<ConvictionView>('workbench');
  const [selectedThesisId, setSelectedThesisId] = useState<string | null>(null);
  const [researchTicker, setResearchTicker] = useState('');
  const [authOpen, setAuthOpen] = useState(false);
  const { user, signOut } = useAuth();
  const { data: health, isError: isHealthError, isLoading: healthLoading } = useHealthCheck();
  const backendStatus =
    health?.status === 'ok' || health?.status === 'degraded' ? 'online' : isHealthError ? 'offline' : healthLoading ? 'checking' : 'offline';

  return (
    <>
      <DeskShell
        view={view}
        onViewChange={setView}
        backendStatus={backendStatus}
        userEmail={user?.email}
        onSignIn={() => setAuthOpen(true)}
        onSignOut={() => void signOut()}
      >
        {view === 'workbench' ? (
          <ThesisWorkbench
            selectedThesisId={selectedThesisId}
            onSelectThesis={setSelectedThesisId}
            onCreateFromResearch={(ticker) => {
              setResearchTicker(ticker ?? '');
              setView('research');
            }}
          />
        ) : null}

        {view === 'research' ? (
          <ResearchRoom
            initialTicker={researchTicker}
            onThesisCreated={(thesis) => {
              setSelectedThesisId(thesis.id);
              setResearchTicker('');
              setView('workbench');
            }}
          />
        ) : null}

        {view === 'alerts' ? (
          <AlertsQueue
            onOpenThesis={(thesisId) => {
              setSelectedThesisId(thesisId);
              setView('workbench');
            }}
          />
        ) : null}
      </DeskShell>

      <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} />
    </>
  );
}
