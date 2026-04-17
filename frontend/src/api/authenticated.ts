import axios, { type AxiosInstance } from 'axios';
import { API_BASE_URL } from '../config/env';
import { supabase } from '../utils/supabase';

export async function getAccessToken(): Promise<string | null> {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export async function getAuthHeader(): Promise<{ Authorization: string } | {}> {
  const accessToken = await getAccessToken();
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

export async function createAuthenticatedClient(): Promise<AxiosInstance> {
  const headers = await getAuthHeader();
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  });
}
