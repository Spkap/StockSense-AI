/**
 * Streaming Debate Analysis Hook
 * Phase 3: Progressive rendering of adversarial debate using SSE
 */

import { useState, useCallback, useRef } from 'react';
import type { DebateAnalysisResult } from '../types/debate';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export type DebateEventType = 
  | 'debate_started'
  | 'tool_started'
  | 'tool_completed'
  | 'bull_drafting'
  | 'bear_drafting'
  | 'bull_complete'
  | 'bear_complete'
  | 'rebuttal_round'
  | 'progress'
  | 'synthesis_started'
  | 'debate_completed'
  | 'error';

export interface DebateStreamEvent {
  type: DebateEventType;
  tool: string | null;
  progress: number;
  message: string;
  timestamp: string;
  data?: Partial<DebateAnalysisResult>;
}

export interface DebatePhase {
  id: DebateEventType;
  label: string;
  status: 'pending' | 'active' | 'complete';
  message?: string;
}

export interface DebateStreamingState {
  isStreaming: boolean;
  progress: number;
  currentPhase: DebateEventType | null;
  phases: DebatePhase[];
  events: DebateStreamEvent[];
  bullConfidence: number | null;
  bearConfidence: number | null;
  rebuttalCount: { bull: number; bear: number } | null;
  error: string | null;
  finalData: DebateAnalysisResult | null;
}

const initialPhases: DebatePhase[] = [
  { id: 'debate_started', label: 'Starting Debate', status: 'pending' },
  { id: 'tool_started', label: 'Collecting Data', status: 'pending' },
  { id: 'bull_drafting', label: 'Bull Analyst Drafting', status: 'pending' },
  { id: 'bear_drafting', label: 'Bear Analyst Drafting', status: 'pending' },
  { id: 'rebuttal_round', label: 'Cross-Examination', status: 'pending' },
  { id: 'synthesis_started', label: 'Synthesizing Verdict', status: 'pending' },
  { id: 'debate_completed', label: 'Debate Complete', status: 'pending' },
];

const initialState: DebateStreamingState = {
  isStreaming: false,
  progress: 0,
  currentPhase: null,
  phases: initialPhases,
  events: [],
  bullConfidence: null,
  bearConfidence: null,
  rebuttalCount: null,
  error: null,
  finalData: null,
};

export function useStreamingDebate() {
  const [state, setState] = useState<DebateStreamingState>(initialState);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startDebate = useCallback((ticker: string) => {
    // Reset state with fresh phases
    setState({ 
      ...initialState, 
      isStreaming: true,
      phases: initialPhases.map(p => ({ ...p, status: 'pending' as const }))
    });

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const url = `${API_BASE_URL}/analyze/debate/${ticker.toUpperCase()}/stream`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data: DebateStreamEvent = JSON.parse(event.data);
        
        setState(prev => {
          const newState = {
            ...prev,
            events: [...prev.events, data],
            progress: data.progress,
            currentPhase: data.type,
          };

          // Update phases based on event type
          const phaseIndex = newState.phases.findIndex(p => p.id === data.type);
          if (phaseIndex !== -1) {
            newState.phases = newState.phases.map((phase, idx) => {
              if (idx < phaseIndex) {
                return { ...phase, status: 'complete' as const };
              } else if (idx === phaseIndex) {
                return { ...phase, status: 'active' as const, message: data.message };
              }
              return phase;
            });
          }

          // Handle specific event types
          switch (data.type) {
            case 'bull_complete':
              if (data.data?.bull_case) {
                newState.bullConfidence = (data.data as any).confidence || null;
              }
              // Also update phases to mark bull as complete
              newState.phases = newState.phases.map(p => 
                p.id === 'bull_drafting' ? { ...p, status: 'complete' as const } : p
              );
              break;
            
            case 'bear_complete':
              if (data.data?.bear_case) {
                newState.bearConfidence = (data.data as any).confidence || null;
              }
              // Also update phases to mark bear as complete
              newState.phases = newState.phases.map(p => 
                p.id === 'bear_drafting' ? { ...p, status: 'complete' as const } : p
              );
              break;
            
            case 'progress':
              // After rebuttal round
              if (data.data) {
                newState.rebuttalCount = {
                  bull: (data.data as any).bull_rebuttals_count || 0,
                  bear: (data.data as any).bear_rebuttals_count || 0,
                };
              }
              break;
            
            case 'debate_completed':
              newState.isStreaming = false;
              newState.phases = newState.phases.map(p => ({ ...p, status: 'complete' as const }));
              if (data.data) {
                newState.finalData = data.data as DebateAnalysisResult;
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

  const stopDebate = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isStreaming: false,
    }));
  }, []);

  const reset = useCallback(() => {
    stopDebate();
    setState(initialState);
  }, [stopDebate]);

  return {
    ...state,
    startDebate,
    stopDebate,
    reset,
  };
}

export default useStreamingDebate;
