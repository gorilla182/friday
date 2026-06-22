// ===== LAYOUT: sidebar + topbar shared across authenticated pages =====

function renderLayout({ active, pageTitleMini }) {
  const navItems = [
    { key: 'dashboard', href: 'dashboard.html', label: 'Дашборд', testid: 'nav-dashboard',
      icon: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>' },
    { key: 'catalog', href: 'catalog.html', label: 'Каталог', testid: 'nav-catalog',
      icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>' },
    { key: 'cart', href: 'cart.html', label: 'Корзина', testid: 'nav-cart',
      icon: '<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M3 4h2l2.4 12.2a2 2 0 0 0 2 1.6h8.2a2 2 0 0 0 2-1.6L21 8H6"/>',
      badge: true },
    { key: 'profile', href: 'profile.html', label: 'Профиль', testid: 'nav-profile',
      icon: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/>' },
  ];

  const navHtml = navItems.map(item => `
    <a href="${item.href}" class="nav-link ${item.key === active ? 'active' : ''}" data-testid="${item.testid}">
      <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${item.icon}</svg></span>
      <span class="label">${item.label}</span>
      ${item.badge ? `<span class="nav-badge" data-testid="nav-cart-badge" style="display:none">0</span>` : ''}
    </a>
  `).join('');

  return `
    <div class="app">
      <aside class="sidebar" data-testid="sidebar">
        <div class="brand">
          <div class="brand-mark"></div>
          <span class="brand-name">QA<span>Store</span></span>
        </div>
        <nav>
          <div class="nav-section-label">Меню</div>
          <div class="nav-list">${navHtml}</div>
        </nav>
        <div class="sidebar-foot">
          <a href="profile.html" class="user-chip" data-testid="sidebar-user-chip">
            <div class="user-avatar">${(window.CURRENT_USER || {}).initials || ''}</div>
            <div class="user-meta">
              <div class="user-name" data-testid="sidebar-user-name">${(window.CURRENT_USER || {}).name || ''}</div>
              <div class="user-email" data-testid="sidebar-user-email">${(window.CURRENT_USER || {}).email || ''}</div>
            </div>
          </a>
        </div>
      </aside>

      <header class="topbar" data-testid="topbar">
        <span class="page-title-mini">${pageTitleMini}</span>
        <div class="search-box">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input type="text" placeholder="Поиск товаров…" data-testid="global-search-input" autocomplete="off">
        </div>
        <div class="topbar-actions">
          <a href="cart.html" class="icon-btn" data-testid="topbar-cart-link" aria-label="Корзина">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M3 4h2l2.4 12.2a2 2 0 0 0 2 1.6h8.2a2 2 0 0 0 2-1.6L21 8H6"/></svg>
            <span class="dot" data-testid="topbar-cart-badge" style="display:none">0</span>
          </a>
          <a href="profile.html" class="icon-btn" data-testid="topbar-profile-link" aria-label="Профиль">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/></svg>
          </a>
        </div>
      </header>

      <main class="main" id="main-content" data-testid="main-content"></main>
    </div>
  `;
}

function mountLayout(opts) {
  document.getElementById('app-root').innerHTML = renderLayout(opts);
  Store.updateCartBadge();
}
