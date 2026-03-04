/**
 * Centralised environment configuration.
 * All VITE_* env vars are resolved here — import from this file, never inline.
 */
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';
