// ===== STORE: minimal UI (cart state for badges only; real cart via Supabase)
// Legacy mock kept ONLY for badge + some compat in renderers. Real data in supabase-data.
const Store = {
  _cart: {},
  getCart() { return { ...this._cart }; },
  setQty(id, qty) { this._cart[id] = qty; this.updateCartBadge(); },
  addToCart(id, qty=1) { this._cart[id] = (this._cart[id]||0) + qty; this.updateCartBadge(); },
  removeFromCart(id) { delete this._cart[id]; this.updateCartBadge(); },
  clearCart() { this._cart = {}; this.updateCartBadge(); },
  cartCount() { return Object.values(this._cart).reduce((a,b)=>a+b,0); },
  updateCartBadge() {
    const c = this.cartCount();
    document.querySelectorAll('[data-testid="nav-cart-badge"]').forEach(el => {
      el.textContent = c;
      el.style.display = c > 0 ? '' : 'none';
    });
    document.querySelectorAll('[data-testid="topbar-cart-badge"]').forEach(el => {
      el.textContent = c;
      el.style.display = c > 0 ? '' : 'none';
    });
  },
};

document.addEventListener('DOMContentLoaded', () => {
  Store.updateCartBadge();
});

window.Store = Store;
