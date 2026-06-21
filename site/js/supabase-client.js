// Shared Supabase client + helpers for the static site
// Update these if you change projects (publishable key is safe to expose)

window.SUPABASE_URL = 'https://fvxhcfisnsganugrgqnm.supabase.co';
window.SUPABASE_ANON_KEY = 'sb_publishable_Vmw74XMZBjinMVYEoJu6FA_K6lU2fMk';

window.createSupabaseClient = () => {
  if (!window.supabase) {
    console.error('Supabase JS not loaded. Include the CDN script.');
    return null;
  }
  return window.supabase.createClient(
    window.SUPABASE_URL,
    window.SUPABASE_ANON_KEY
  );
};

// Helper to require auth
window.requireAuth = async (client) => {
  const { data: { user } } = await client.auth.getUser();
  if (!user) {
    window.location.href = 'index.html';
    return null;
  }
  return user;
};

// Global error helper
window.showError = (message, elementId = 'error-message') => {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
  } else {
    alert(message);
  }
};

window.hideError = (elementId = 'error-message') => {
  const el = document.getElementById(elementId);
  if (el) el.style.display = 'none';
};

// Simple loading helper
window.setLoading = (button, isLoading, originalText = 'Submit') => {
  if (!button) return;
  if (isLoading) {
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.textContent = 'Loading...';
  } else {
    button.disabled = false;
    button.textContent = button.dataset.originalText || originalText;
  }
};