// Shared Supabase client and helpers for the static site
// Update these values when deploying (or use env in a build step)

window.SUPABASE_URL = 'https://fvxhcfisnsganugrgqnm.supabase.co';
window.SUPABASE_KEY = 'sb_publishable_Vmw74XMZBjinMVYEoJu6FA_K6lU2fMk';

window.createSupabaseClient = () => {
  return window.supabase.createClient(
    window.SUPABASE_URL,
    window.SUPABASE_KEY
  );
};

// Helper to require auth (redirect to login if not logged in)
window.requireAuth = async (supabase) => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    window.location.href = 'index.html';
    return null;
  }
  return user;
};

// Show error helper (matches original data-testid="error-message")
window.showError = (message, elementId = 'error-message') => {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
    el.style.display = 'block';
  }
};

window.hideError = (elementId = 'error-message') => {
  const el = document.getElementById(elementId);
  if (el) el.style.display = 'none';
};
