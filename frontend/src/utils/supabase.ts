/**
 * Supabase client for frontend auth and data operations.
 * Stage 3: User Belief System
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js';

// Environment variables (set in .env or Vite config)
const supabaseUrl = typeof import.meta.env.VITE_SUPABASE_URL === 'string'
  ? import.meta.env.VITE_SUPABASE_URL.trim()
  : '';
const supabaseAnonKey = typeof import.meta.env.VITE_SUPABASE_ANON_KEY === 'string'
  ? import.meta.env.VITE_SUPABASE_ANON_KEY.trim()
  : '';

export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey);
export const supabaseConfigError = isSupabaseConfigured
  ? null
  : 'Missing Supabase credentials. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.';

// Create Supabase client
export const supabase: SupabaseClient = createClient(
  isSupabaseConfigured ? supabaseUrl : 'https://example.supabase.co',
  isSupabaseConfigured ? supabaseAnonKey : 'missing-anon-key',
  isSupabaseConfigured
    ? undefined
    : {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false,
        },
      }
);

// Auth helper functions
export async function signInWithGoogle() {
  if (!isSupabaseConfigured) {
    return { data: null, error: new Error(supabaseConfigError ?? 'Supabase is not configured') };
  }

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.origin,
    },
  });
  return { data, error };
}

export async function signInWithEmail(email: string, password: string) {
  if (!isSupabaseConfigured) {
    return { data: null, error: new Error(supabaseConfigError ?? 'Supabase is not configured') };
  }

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });
  return { data, error };
}

export async function signUpWithEmail(email: string, password: string) {
  if (!isSupabaseConfigured) {
    return { data: null, error: new Error(supabaseConfigError ?? 'Supabase is not configured') };
  }

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });
  return { data, error };
}

export async function signOut() {
  if (!isSupabaseConfigured) {
    return { error: null };
  }

  const { error } = await supabase.auth.signOut();
  return { error };
}

export async function getSession() {
  if (!isSupabaseConfigured) {
    return { session: null, error: new Error(supabaseConfigError ?? 'Supabase is not configured') };
  }

  const { data, error } = await supabase.auth.getSession();
  return { session: data.session, error };
}

export async function getCurrentUser() {
  if (!isSupabaseConfigured) {
    return { user: null, error: new Error(supabaseConfigError ?? 'Supabase is not configured') };
  }

  const { data, error } = await supabase.auth.getUser();
  return { user: data.user, error };
}
