import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import type { DebateAnalysisResponse } from '../types/debate';
import { API_BASE_URL } from '../config/env';

async function fetchDebateAnalysis(ticker: string): Promise<DebateAnalysisResponse> {
  const { data } = await axios.get<DebateAnalysisResponse>(`${API_BASE_URL}/analyze/debate/${ticker.toUpperCase()}`);
  return data;
}

export function useDebateAnalysis() {
  return useMutation({
    mutationFn: fetchDebateAnalysis,
  });
}
