/**
 * Streaming Analysis Hook
 * Stage 4: Progressive rendering of analysis results using SSE
 */

import { useState, useCallback, useRef } from 'react';
import type { AnalysisData } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

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
  const eventSourceRef = useRef<EventSource | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const startAnalysis = useCallback((ticker: string) => {
    // Reset state
    setState({ ...initialState, isStreaming: true });

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = `${API_BASE_URL}/analyze/${ticker.toUpperCase()}/stream`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data);
        
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
              if (data.data) {
                newState.finalData = data.data as AnalysisData;
                newState.partialData = data.data;
              }
              eventSource.close();
              break;
            
            case 'error':
              newState.isStreaming = false;
              newState.error = data.message;
              eventSource.close();
              break;
          }

          return newState;
        });
      } catch (e) {
        console.error('Failed to parse SSE event:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: 'Connection to server lost',
      }));
      eventSource.close();
    };

  }, []);

  const stopAnalysis = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
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
