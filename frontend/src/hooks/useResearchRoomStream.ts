import { useCallback, useRef, useState } from 'react';
import { API_BASE_URL } from '../config/env';
import { getAccessToken } from '../api/authenticated';
import { cancelResearchRoomRun, getResearchRoomRun } from '../api/researchRoom';
import type { ResearchRoomFinal, ResearchRoomRunBundle, RunStreamEvent } from '../types/researchRoom';

interface ResearchRoomState {
  isStreaming: boolean;
  activeRunId: string | null;
  progress: number;
  phase: string | null;
  events: RunStreamEvent[];
  finalData: ResearchRoomFinal | null;
  runBundle: ResearchRoomRunBundle | null;
  error: string | null;
}

const initialState: ResearchRoomState = {
  isStreaming: false,
  activeRunId: null,
  progress: 0,
  phase: null,
  events: [],
  finalData: null,
  runBundle: null,
  error: null,
};

export function useResearchRoomStream() {
  const [state, setState] = useState<ResearchRoomState>(initialState);
  const abortRef = useRef<AbortController | null>(null);
  const activeRunIdRef = useRef<string | null>(null);

  const loadRun = useCallback(async (runId: string) => {
    try {
      const bundle = await getResearchRoomRun(runId);
      setState(prev => ({
        ...prev,
        runBundle: bundle,
        finalData: bundle.run?.final_result ?? prev.finalData,
      }));
    } catch {
      // Run recovery should not break the active stream UI.
    }
  }, []);

  const start = useCallback(async (ticker: string, question: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    activeRunIdRef.current = null;
    setState(initialState);
    setState(prev => ({ ...prev, isStreaming: true }));

    try {
      const token = await getAccessToken();
      if (!token) {
        setState({ ...initialState, error: 'Sign in required to use Research Room' });
        return;
      }

      const response = await fetch(
        `${API_BASE_URL}/api/research-room/${encodeURIComponent(ticker)}/stream?question=${encodeURIComponent(question)}`,
        {
          method: 'GET',
          headers: {
            Accept: 'text/event-stream',
            Authorization: `Bearer ${token}`,
          },
          signal: controller.signal,
        }
      );

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
          const event = JSON.parse(line.slice(6)) as RunStreamEvent;
          activeRunIdRef.current = event.run_id;

          setState(prev => ({
            ...prev,
            activeRunId: event.run_id,
            isStreaming: event.type !== 'completed' && event.type !== 'cancelled' && event.type !== 'error',
            progress: event.progress,
            phase: event.phase,
            events: [...prev.events, event],
            finalData: event.type === 'completed' ? event.data as unknown as ResearchRoomFinal : prev.finalData,
            error: event.type === 'error' ? event.message : prev.error,
          }));

          if (event.type === 'completed' || event.type === 'cancelled' || event.type === 'error') {
            await reader.cancel();
            if (event.type === 'completed' || event.type === 'cancelled') {
              await loadRun(event.run_id);
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
        error: err instanceof Error ? err.message : 'Connection to Research Room lost',
      }));
    }
  }, [loadRun]);

  const stop = useCallback(async () => {
    const runId = activeRunIdRef.current;
    abortRef.current?.abort();
    abortRef.current = null;
    if (runId) {
      try {
        await cancelResearchRoomRun(runId);
      } catch {
        // Local abort still stops the stream if persisted cancellation fails.
      }
    }
    setState(prev => ({ ...prev, isStreaming: false }));
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    activeRunIdRef.current = null;
    setState(initialState);
  }, []);

  return { ...state, start, stop, reset, loadRun };
}
