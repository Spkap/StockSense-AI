/**
 * Centralised environment configuration.
 * All VITE_* env vars are resolved here — import from this file, never inline.
 */
function readEnv(name: string): string | undefined {
  const value = import.meta.env[name];
  return typeof value === 'string' ? value.trim() : undefined;
}

function resolveApiBaseUrl(): string {
  const configured = readEnv('VITE_API_URL');
  const fallback = 'http://127.0.0.1:8000';

  // Local frontend development should talk to the local backend by default,
  // even if a checked-in .env points at a deployed API URL.
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    const isLocalFrontend = host === '127.0.0.1' || host === 'localhost';
    if (isLocalFrontend) {
      return fallback;
    }
  }

  if (configured) {
    return configured;
  }

  throw new Error('VITE_API_URL is required outside local development. Set it to the deployed StockSense API URL.');
}

export const API_BASE_URL: string = resolveApiBaseUrl();
