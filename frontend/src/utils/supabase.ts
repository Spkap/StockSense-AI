/**
 * Supabase client for frontend auth and data operations.
 * Stage 3: User Belief System
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js';

// Environment variables (set in .env or Vite config)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    'Missing Supabase credentials. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env'
  );
}

// Create Supabase client
export const supabase: SupabaseClient | null = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

const configurationError = () => new Error("Login is unavailable until Supabase is configured.");

// Auth helper functions
export async function signInWithGoogle() {
  if (!supabase) return { data: null, error: configurationError() };
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin,
    },
  });
  return { data, error };
}

export async function signInWithEmail(email: string, password: string) {
  if (!supabase) return { data: null, error: configurationError() };
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  return { data, error };
}

export async function signUpWithEmail(email: string, password: string) {
  if (!supabase) return { data: null, error: configurationError() };
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });
  return { data, error };
}

export async function signOut() {
  if (!supabase) return { error: null };
  const { error } = await supabase.auth.signOut();
  return { error };
}

export async function getSession() {
  if (!supabase) return { session: null, error: null };
  const { data, error } = await supabase.auth.getSession();
  return { session: data.session, error };
}

export async function getCurrentUser() {
  if (!supabase) return { user: null, error: null };
  const { data, error } = await supabase.auth.getUser();
  return { user: data.user, error };
}
