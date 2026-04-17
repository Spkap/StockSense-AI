/**
 * Streaming Analysis Hook
 * Stage 4: Progressive rendering of analysis results using SSE
 *
 * Uses fetch() + ReadableStream instead of EventSource so we can send
 * the Authorization header for kill criteria monitoring.
 */

import { useState, useCallback, useRef } from 'react';
import type { AnalysisData } from '../types/api';
import { API_BASE_URL } from '../config/env';
import { supabase } from '../utils/supabase';

export type StreamEventType =
  | 'started'
  | 'tool_started'
  | 'tool_completed'
  | 'progress'
  | 'completed'
  | 'error';

export interface StreamEvent {
  type: StreamEventType;
  tool: string | null;
  progress: number;
  message: string;
  timestamp: string;
  data?: Partial<AnalysisData>;
}

export interface StreamingState {
  isStreaming: boolean;
  progress: number;
  currentTool: string | null;
  events: StreamEvent[];
  partialData: Partial<AnalysisData>;
  error: string | null;
  finalData: AnalysisData | null;
}

const initialState: StreamingState = {
  isStreaming: false,
  progress: 0,
  currentTool: null,
  events: [],
  partialData: {},
  error: null,
  finalData: null,
};

export function useStreamingAnalysis() {
  const [state, setState] = useState<StreamingState>(initialState);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startAnalysis = useCallback(async (ticker: string) => {
    // Reset state
    setState({ ...initialState, isStreaming: true });

    // Abort any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const url = `${API_BASE_URL}/analyze/${ticker.toUpperCase()}/stream`;

    // Get auth token if user is logged in
    const headers: Record<string, string> = {
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    };
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
      }
    } catch {
      // Not authenticated — kill criteria monitoring won't run, analysis still works
    }

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Server responded ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE lines end with \n\n
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data: ')) continue;

          try {
            const data: StreamEvent = JSON.parse(line.slice(6));

            setState(prev => {
              const newState = {
                ...prev,
                events: [...prev.events, data],
                progress: data.progress,
                currentTool: data.tool || prev.currentTool,
              };

              switch (data.type) {
                case 'started':
                  newState.currentTool = null;
                  break;

                case 'tool_started':
                  newState.currentTool = data.tool;
                  break;

                case 'tool_completed':
                  if (data.data) {
                    newState.partialData = { ...prev.partialData, ...data.data };
                  }
                  break;

                case 'completed':
                  newState.isStreaming = false;
                  newState.currentTool = null;
                  if (data.data) {
                    newState.finalData = data.data as AnalysisData;
                    newState.partialData = data.data;
                  }
                  break;

                case 'error':
                  newState.isStreaming = false;
                  newState.error = data.message;
                  break;
              }

              return newState;
            });

            if (data.type === 'completed' || data.type === 'error') {
              reader.cancel();
              break;
            }
          } catch {
            // Malformed SSE line — skip
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: err instanceof Error ? err.message : 'Connection to server lost',
      }));
    }
  }, []);

  const stopAnalysis = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState(prev => ({ ...prev, isStreaming: false }));
  }, []);

  const reset = useCallback(() => {
    stopAnalysis();
    setState(initialState);
  }, [stopAnalysis]);

  return {
    ...state,
    startAnalysis,
    stopAnalysis,
    reset,
  };
}

export default useStreamingAnalysis;
