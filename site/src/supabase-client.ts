// Shared Supabase client + helpers for the static site
// Update these if you change projects (publishable key is safe to expose)

declare const supabase: any; // from CDN

interface SupabaseClient {
  auth: any;
  from: (table: string) => any;
}

(window as any).SUPABASE_URL = 'https://fvxhcfisnsganugrgqnm.supabase.co';
(window as any).SUPABASE_ANON_KEY = 'sb_publishable_Vmw74XMZBjinMVYEoJu6FA_K6lU2fMk';

(window as any).createSupabaseClient = (): SupabaseClient | null => {
  if (!(window as any).supabase) {
    console.error('Supabase JS not loaded. Include the CDN script.');
    return null;
  }
  return (window as any).supabase.createClient(
    (window as any).SUPABASE_URL,
    (window as any).SUPABASE_ANON_KEY
  );
};

// Helper to require auth
(window as any).requireAuth = async (client: SupabaseClient): Promise<any | null> => {
  const { data: { user } } = await client.auth.getUser();
  if (!user) {
    window.location.href = 'index.html';
    return null;
  }
  return user;
};

// Global error helper
(window as any).showError = (message: string, elementId: string = 'error-message'): void => {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
  } else {
    alert(message);
  }
};

(window as any).hideError = (elementId: string = 'error-message'): void => {
  const el = document.getElementById(elementId);
  if (el) el.style.display = 'none';
};

// Simple loading helper
(window as any).setLoading = (button: HTMLButtonElement | null, isLoading: boolean, originalText: string = 'Submit'): void => {
  if (!button) return;
  if (isLoading) {
    button.disabled = true;
    (button as any).dataset.originalText = button.textContent;
    button.textContent = 'Loading...';
  } else {
    button.disabled = false;
    button.textContent = (button as any).dataset.originalText || originalText;
  }
};