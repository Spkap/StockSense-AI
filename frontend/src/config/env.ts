/**
 * Centralised environment configuration.
 * All VITE_* env vars are resolved here — import from this file, never inline.
 */
function readEnv(name: string): string | undefined {
  const value = import.meta.env[name];
  return typeof value === 'string' ? value.trim() : undefined;
}

export const API_BASE_URL: string = readEnv('VITE_API_URL') || 'http://127.0.0.1:8000';
