/**
 * Streaming Analysis Hook
 * Stage 4: Progressive rendering of analysis results using SSE
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { AnalysisData } from '../types/api';
import { API_BASE_URL } from '../config/env';
import { supabase } from '../utils/supabase';
import { useAuth } from '../context/AuthContext';

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
  const { user } = useAuth();
  const [state, setState] = useState<StreamingState>(initialState);
  const eventSourceRef = useRef<AbortController | null>(null);
  useEffect(() => () => { eventSourceRef.current?.abort(); }, []);

  const startAnalysis = useCallback(async (ticker: string) => {
    // Reset state
    setState({ ...initialState, isStreaming: true });

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
    }

    const controller = new AbortController();
    eventSourceRef.current = controller;
    try {
      const { data: { session }, error: sessionError } = supabase ? await supabase.auth.getSession() : { data: { session: null }, error: null };
      if (sessionError || (session?.user.id || null) !== (user?.id || null)) throw new Error('Session unavailable');
      if (controller.signal.aborted) return;
      const response = await fetch(`${API_BASE_URL}/analyze/${encodeURIComponent(ticker.toUpperCase())}/stream`, {
        signal: controller.signal,
        headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
      });
      if (!response.ok || !response.body) throw new Error('Connection failed');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let terminal = false;
      while (!terminal) {
        const chunk = await reader.read();
        if (controller.signal.aborted || eventSourceRef.current !== controller) return;
        buffer += decoder.decode(chunk.value, { stream: !chunk.done });
        const blocks = buffer.split(/\r?\n\r?\n/);
        buffer = blocks.pop() || '';
        for (const block of blocks) {
          const line = block.split(/\r?\n/).find(item => item.startsWith('data:'));
          if (!line) continue;
          const data: StreamEvent = JSON.parse(line.slice(5).trim());
          if (data.type === 'completed' || data.type === 'error') terminal = true;
        setState(prev => {
          const newState = {
            ...prev,
            events: [...prev.events, data],
            progress: data.progress,
            currentTool: data.tool || prev.currentTool,
          };

          // Handle different event types
          switch (data.type) {
            case 'started':
              newState.currentTool = null;
              break;
            
            case 'tool_started':
              newState.currentTool = data.tool;
              break;
            
            case 'tool_completed':
              // Merge partial data
              if (data.data) {
                newState.partialData = {
                  ...prev.partialData,
                  ...data.data,
                };
              }
              break;
            
            case 'completed':
              newState.isStreaming = false;
              newState.currentTool = null;
              if (data.data && typeof data.data.ticker === 'string' && data.data.ticker.toUpperCase() === ticker.toUpperCase()
                  && typeof data.data.summary === 'string' && data.data.summary.trim()
                  && Array.isArray(data.data.headlines) && Array.isArray(data.data.price_data)) {
                newState.finalData = data.data as AnalysisData;
                newState.partialData = data.data;
              } else {
                newState.error = 'The server returned an incomplete analysis. Please retry.';
              }
              break;
            
            case 'error':
              newState.isStreaming = false;
              newState.error = data.message;
              break;
          }

          return newState;
        });
        }
        if (chunk.done) break;
      }
      if (!terminal && !controller.signal.aborted) throw new Error('Stream ended early');
      if (eventSourceRef.current === controller) eventSourceRef.current = null;
    } catch (error) {
      if (controller.signal.aborted || eventSourceRef.current !== controller) return;
      console.error('Analysis stream failed:', error);
      eventSourceRef.current = null;
      setState(prev => ({ ...prev, isStreaming: false, error: 'Connection lost. Check your connection and try again.' }));
    }

  }, [user?.id]);

  const stopAnalysis = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.abort();
      eventSourceRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isStreaming: false,
    }));
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
