// ===== BOOTSTRAP: common initialization for authenticated pages =====
// Reduces massive duplication across dashboard, catalog, cart, profile, item_detail

window.initAuthenticatedPage = async function(pageName, pageTitle, renderFn) {
  try {
    const client = window.createSupabaseClient();
    if (!client) return;

    const user = await window.requireAuth(client);
    if (!user) return;

    const currentUser = await window.loadCurrentUser(client) || { 
      name: 'User', 
      initials: 'U', 
      email: user.email || '' 
    };
    window.CURRENT_USER = currentUser;

    // Sync cart early for badges and UI decisions
    await window.syncStoreFromDB(client, user.id);

    mountLayout({ active: pageName, pageTitleMini: pageTitle });

    // Call page-specific render logic
    if (typeof renderFn === 'function') {
      await renderFn({ client, user, currentUser });
    }
  } catch (e) {
    console.error(`Error initializing ${pageName} page:`, e);
    document.body.innerHTML = `
      <div data-testid="error-state" style="padding:2rem;text-align:center;">
        Error loading ${pageName}: ${e && e.message ? e.message : e}. 
        <a href="index.html">Go to login</a>
      </div>
    `;
  }
};
