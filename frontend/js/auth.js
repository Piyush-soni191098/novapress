// Auth module — wraps Supabase JS SDK
// Supabase client is loaded from window.supabase (set up in config.js)

import { toast, getSupabaseConfig } from "./utils.js";

let _client = null;

function getClient() {
  if (_client) return _client;
  const { url, anonKey } = getSupabaseConfig();
  if (!url || !anonKey) {
    console.warn("[auth] Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY in config.js");
    return null;
  }
  if (window.supabase?.createClient) {
    _client = window.supabase.createClient(url, anonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }
  return _client;
}

export async function getSession() {
  const client = getClient();
  if (!client) return null;
  const { data } = await client.auth.getSession();
  return data.session;
}

export async function getUser() {
  const client = getClient();
  if (!client) return null;
  const { data } = await client.auth.getUser();
  return data.user || null;
}

export async function getToken() {
  // Primary: Supabase SDK session
  const session = await getSession();
  if (session?.access_token) return session.access_token;

  // Fallback: read directly from localStorage (covers edge cases where
  // the SDK client doesn't restore the session on a new page load)
  try {
    const { url } = getSupabaseConfig();
    const ref = url?.match(/\/\/([^.]+)\./)?.[1];
    if (ref) {
      const raw = localStorage.getItem(`sb-${ref}-auth-token`);
      if (raw) {
        const parsed = JSON.parse(raw);
        const token = parsed?.access_token;
        if (token) {
          console.debug("[auth] token restored from localStorage");
          return token;
        }
      }
    }
  } catch {}
  console.warn("[auth] getToken: no session found");
  return null;
}

export async function signUp(email, password) {
  const client = getClient();
  if (!client) throw new Error("Auth not configured");
  const { data, error } = await client.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: `${location.origin}/onboarding.html` },
  });
  if (error) throw error;
  return data;
}

export async function signIn(email, password) {
  const client = getClient();
  if (!client) throw new Error("Auth not configured");
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signOut() {
  const client = getClient();
  if (!client) return;
  await client.auth.signOut();
  localStorage.removeItem("signal-session-hint");
}

export async function resetPasswordForEmail(email) {
  const client = getClient();
  if (!client) throw new Error("Auth not configured");
  const { error } = await client.auth.resetPasswordForEmail(email, {
    redirectTo: `${location.origin}/reset-password.html`,
  });
  if (error) throw error;
}

export async function updatePassword(newPassword) {
  const client = getClient();
  if (!client) throw new Error("Auth not configured");
  const { error } = await client.auth.updateUser({ password: newPassword });
  if (error) throw error;
}

export async function resendVerification(email) {
  const client = getClient();
  if (!client) throw new Error("Auth not configured");
  const { error } = await client.auth.resend({ type: "signup", email });
  if (error) throw error;
}

export async function verifyOtp(email, token) {
  const client = getClient();
  if (!client) throw new Error("Auth not configured");
  const { data, error } = await client.auth.verifyOtp({ email, token, type: "signup" });
  if (error) throw error;
  return data;
}

export function onAuthStateChange(callback) {
  const client = getClient();
  if (!client) return () => {};
  const { data: { subscription } } = client.auth.onAuthStateChange(callback);
  return () => subscription.unsubscribe();
}

// Guard — call at the top of any protected page
export async function requireAuth(redirectTo = "/login.html") {
  const session = await getSession();
  if (!session) {
    location.replace(redirectTo);
    return null;
  }
  return session;
}

// Guard — redirect authenticated users away from auth pages
export async function redirectIfAuthenticated(redirectTo = "/dashboard.html") {
  const session = await getSession();
  if (session) location.replace(redirectTo);
}

// Check if onboarding is needed (based on profile)
export async function needsOnboarding() {
  const client = getClient();
  if (!client) return false;
  const user = await getUser();
  if (!user) return false;
  try {
    const { data } = await client
      .from("profiles")
      .select("onboarding_complete")
      .eq("id", user.id)
      .single();
    return !data?.onboarding_complete;
  } catch {
    return false;
  }
}
