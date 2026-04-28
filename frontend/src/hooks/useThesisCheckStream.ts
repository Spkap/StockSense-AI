import { useCallback, useRef, useState } from 'react';
import { API_BASE_URL } from '../config/env';
import { supabase } from '../utils/supabase';
import type { ThesisCheckFinal, ThesisCheckRunBundle, ThesisCheckStreamEvent, ThesisCorrectionRequest } from '../types/thesisCheck';

interface ThesisCheckState {
  isStreaming: boolean;
  activeRunId: string | null;
  progress: number;
  phase: string | null;
  events: ThesisCheckStreamEvent[];
  finalData: ThesisCheckFinal | null;
  runBundle: ThesisCheckRunBundle | null;
  error: string | null;
}

const initialState: ThesisCheckState = {
  isStreaming: false,
  activeRunId: null,
  progress: 0,
  phase: null,
  events: [],
  finalData: null,
  runBundle: null,
  error: null,
};

export function useThesisCheckStream() {
  const [state, setState] = useState<ThesisCheckState>(initialState);
  const abortRef = useRef<AbortController | null>(null);
  const activeRunIdRef = useRef<string | null>(null);

  const getAccessToken = useCallback(async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  }, []);

  const loadLatest = useCallback(async (thesisId: string) => {
    const token = await getAccessToken();
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/theses/${thesisId}/check/latest`, {
        headers: {
          Accept: 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) return;
      const bundle = await response.json() as ThesisCheckRunBundle;
      const finalData = bundle.run?.final_result ?? null;
      setState(prev => ({
        ...prev,
        runBundle: bundle,
        finalData: prev.finalData ?? finalData,
        progress: prev.events.length > 0 ? prev.progress : finalData ? 1 : prev.progress,
        phase: prev.events.length > 0 ? prev.phase : finalData ? 'completed' : prev.phase,
      }));
    } catch {
      // Latest-run recovery should never break the primary thesis page.
    }
  }, [getAccessToken]);

  const start = useCallback(async (thesisId: string) => {
    if (abortRef.current) {
      abortRef.current.abort();
    }

    const controller = new AbortController();
    abortRef.current = controller;
    activeRunIdRef.current = null;
    setState(prev => ({ ...initialState, runBundle: prev.runBundle, isStreaming: true }));

    try {
      const token = await getAccessToken();
      if (!token) {
        setState({ ...initialState, error: 'Sign in required to check thesis' });
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/theses/${thesisId}/check/stream`, {
        method: 'GET',
        headers: {
          Accept: 'text/event-stream',
          Authorization: `Bearer ${token}`,
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        setState({ ...initialState, error: `Server responded ${response.status}` });
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        setState({ ...initialState, error: 'No response body' });
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop() ?? '';

        for (const chunk of chunks) {
          const line = chunk.trim();
          if (!line.startsWith('data: ')) continue;

          const event = JSON.parse(line.slice(6)) as ThesisCheckStreamEvent;
          activeRunIdRef.current = event.run_id;

          setState(prev => ({
            ...prev,
            activeRunId: event.run_id,
            isStreaming: event.type !== 'completed' && event.type !== 'cancelled' && event.type !== 'error',
            progress: event.progress,
            phase: event.phase,
            events: [...prev.events, event],
            finalData: event.type === 'completed' ? event.data as unknown as ThesisCheckFinal : prev.finalData,
            error: event.type === 'error' ? event.message : prev.error,
          }));

          if (event.type === 'completed' || event.type === 'cancelled' || event.type === 'error') {
            await reader.cancel();
            if (event.type === 'completed' || event.type === 'cancelled') {
              await loadLatest(thesisId);
            }
            return;
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: err instanceof Error ? err.message : 'Connection to server lost',
      }));
    }
  }, [getAccessToken, loadLatest]);

  const stop = useCallback(async () => {
    const runId = activeRunIdRef.current;
    abortRef.current?.abort();
    abortRef.current = null;
    if (runId) {
      try {
        const token = await getAccessToken();
        if (token) {
          await fetch(`${API_BASE_URL}/api/thesis-runs/${runId}/cancel`, {
            method: 'POST',
            headers: {
              Accept: 'application/json',
              Authorization: `Bearer ${token}`,
            },
          });
        }
      } catch {
        // Client-side stop should still stop the stream even if persisted cancel fails.
      }
    }
    setState(prev => ({ ...prev, isStreaming: false }));
  }, [getAccessToken]);

  const recordCorrection = useCallback(async (runId: string, correction: ThesisCorrectionRequest) => {
    const token = await getAccessToken();
    if (!token) {
      setState(prev => ({ ...prev, error: 'Sign in required to save correction' }));
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/thesis-runs/${runId}/corrections`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(correction),
    });

    if (!response.ok) {
      setState(prev => ({ ...prev, error: `Correction failed with ${response.status}` }));
      return;
    }
  }, [getAccessToken]);

  const reset = useCallback(() => {
    stop();
    setState(initialState);
  }, [stop]);

  return { ...state, start, stop, reset, loadLatest, recordCorrection };
}
