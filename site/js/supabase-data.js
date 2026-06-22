// ===== Supabase Data Layer for QA Store (real DB instead of mocks)
// Maps real tables to the UI shapes expected by design
//
// Sections:
// - Products & Catalog
// - User & Auth helpers
// - Cart operations
// - Orders
// - Reviews
// - API Items (for test API practice)
// - Shared UI helpers (render, format, etc)

// --- Products & Catalog ---
window.loadProducts = async (client) => {
  const { data, error } = await client
    .from('products')
    .select('*')
    .order('id');
  if (error) {
    console.error('loadProducts error', error);
    return [];
  }
  // Map to design shape: id (string for consistency with mocks), name, category, price, stock (default), rating (default), img key
  return (data || []).map(p => ({
    id: String(p.id),
    name: p.name,
    description: p.description || '',
    category: p.category || 'general',
    price: Number(p.price) || 0,
    stock: 10, // default since not in schema, for UI
    rating: 4.5, // default
    img: (p.category || 'general').toLowerCase().includes('test') ? 'tablet' : 'keyboard' // simple mapping
  }));
};

// --- User helpers ---
window.loadCurrentUser = async (client) => {
  const { data: { user } } = await client.auth.getUser();
  if (!user) return null;
  const name = (user.user_metadata?.name || user.email?.split('@')[0] || 'User').toString();
  const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0,2) || 'U';
  return {
    id: user.id,
    name,
    email: user.email,
    plan: 'Tester',
    joined: user.created_at ? new Date(user.created_at).toISOString().split('T')[0] : '',
    initials
  };
};

window.loadApiItems = async (client, userId) => {
  const { data, error } = await client
    .from('api_items')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });
  if (error) {
    console.error('loadApiItems', error);
    return [];
  }
  return (data || []).map(i => ({
    id: String(i.id),
    name: i.title,
    addedAt: i.created_at ? i.created_at.split('T')[0] : '',
    status: 'active', // default
    price: 0, // not in schema, optional
    description: i.description || ''
  }));
};

window.loadCart = async (client, userId) => {
  const { data, error } = await client
    .from('cart_items')
    .select(`
      product_id,
      quantity,
      products (id, name, price)
    `)
    .eq('user_id', userId);
  if (error) {
    console.error('loadCart', error);
    return {};
  }
  const cart = {};
  (data || []).forEach(row => {
    if (row.products) {
      cart[String(row.product_id)] = row.quantity || 1;
    }
  });
  return cart;
};

window.addToCartDB = async (client, userId, productId, qty = 1) => {
  const { error } = await client
    .from('cart_items')
    .upsert({
      user_id: userId,
      product_id: parseInt(productId),
      quantity: qty
    }, { onConflict: 'user_id,product_id' });
  if (error) console.error('addToCartDB', error);
  return !error;
};

window.setCartQtyDB = async (client, userId, productId, qty) => {
  if (qty <= 0) {
    await client.from('cart_items').delete().match({ user_id: userId, product_id: parseInt(productId) });
  } else {
    await client.from('cart_items').update({ quantity: qty }).match({ user_id: userId, product_id: parseInt(productId) });
  }
};

window.removeFromCartDB = async (client, userId, productId) => {
  await client.from('cart_items').delete().match({ user_id: userId, product_id: parseInt(productId) });
};

window.clearCartDB = async (client, userId) => {
  await client.from('cart_items').delete().eq('user_id', userId);
};

// Shared UI helpers to reduce duplication across pages
window.formatPrice = (n) => '$' + (n || 0).toFixed(2);

window.productIcon = (key, size = 40) => {
  const defaultIcon = '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 12h8M12 8v8"/>';
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${defaultIcon}</svg>`;
};

window.renderProductCard = (p, currentQty = 0) => {
  const actions = currentQty > 0
    ? `<div class="product-card-actions">
        <div class="qty-stepper" data-testid="qty-stepper" data-product-id="${p.id}">
          <button data-action="decrement" data-product-id="${p.id}" data-testid="qty-decrement-button" aria-label="Уменьшить">−</button>
          <span class="qty-value" data-testid="qty-value">${currentQty}</span>
          <button data-action="increment" data-product-id="${p.id}" data-testid="qty-increment-button" aria-label="Увеличить">+</button>
        </div>
      </div>`
    : `<div class="product-card-actions">
        <button class="btn btn-primary btn-block" data-testid="add-to-cart-button" data-action="add-to-cart" data-product-id="${p.id}">Добавить в корзину</button>
      </div>`;
  return `
    <div class="product-card" data-testid="product-card" data-product-id="${p.id}">
      <span class="test-tag product-id-tag" data-testid="product-id-tag">${p.id}</span>
      <div class="product-thumb">${window.productIcon(p.img, 40)}</div>
      <div>
        <span class="product-category" data-testid="product-category">${p.category}</span>
        <div class="product-name" data-testid="product-name" data-action="review" data-product-id="${p.id}" style="cursor:pointer;">${p.name}</div>
      </div>
      <div class="product-meta-row">
        <span class="product-price" data-testid="product-price">${window.formatPrice(p.price)}</span>
        <span class="product-rating"><svg width="12" height="12" viewBox="0 0 24 24"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/></svg>${p.rating}</span>
      </div>
      ${actions}
      <button type="button" class="btn btn-ghost btn-sm" data-action="review" data-product-id="${p.id}" data-testid="leave-review-${p.id}" style="margin-top:4px;width:100%;font-size:12px;">Оставить отзыв</button>
    </div>
  `;
};

// Attach handlers for product grids (dashboard recommended or catalog)
// products array, updateStatsCb optional for dashboard stats refresh
window.attachProductGridHandlers = async (grid, client, user, products, updateStatsCb) => {
  grid.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const id = btn.getAttribute('data-product-id');
    const product = products.find(pp => pp.id === id);
    const card = btn.closest('.product-card');
    if (!product || !card) return;

    if (btn.dataset.action === 'add-to-cart') {
      await window.addToCartDB(client, user.id, id, 1);
      window.Store.addToCart(id, 1);
      card.querySelector('.product-card-actions').outerHTML = `
        <div class="product-card-actions">
          <div class="qty-stepper" data-testid="qty-stepper" data-product-id="${id}">
            <button data-action="decrement" data-product-id="${id}" data-testid="qty-decrement-button" aria-label="Уменьшить">−</button>
            <span class="qty-value" data-testid="qty-value">1</span>
            <button data-action="increment" data-product-id="${id}" data-testid="qty-increment-button" aria-label="Увеличить">+</button>
          </div>
        </div>
      `;
      if (window.showToast) window.showToast(`«${product.name}» добавлен в корзину`, 'success');
      if (updateStatsCb) await updateStatsCb();
    } else if (btn.dataset.action === 'increment' || btn.dataset.action === 'decrement') {
      const valEl = card.querySelector('.qty-value');
      if (!valEl) return;
      let v = parseInt(valEl.textContent) || 1;
      if (btn.dataset.action === 'increment') {
        v++;
        valEl.textContent = v;
        await window.setCartQtyDB(client, user.id, id, v);
        window.Store.setQty(id, v);
      } else {
        v = v - 1;
        if (v <= 0) {
          await window.setCartQtyDB(client, user.id, id, 0);
          window.Store.setQty(id, 0);
          card.querySelector('.product-card-actions').outerHTML = `
            <div class="product-card-actions">
              <button class="btn btn-primary btn-block" data-testid="add-to-cart-button" data-action="add-to-cart" data-product-id="${id}">Добавить в корзину</button>
            </div>
          `;
        } else {
          valEl.textContent = v;
          await window.setCartQtyDB(client, user.id, id, v);
          window.Store.setQty(id, v);
        }
      }
      if (updateStatsCb) await updateStatsCb();
    } else if (btn.dataset.action === 'review') {
      window.location.href = `item_detail.html?id=${id}`;
    }
  });
};

// ===== Additional shared cart helpers (dedup for cart.html and flows) =====
window.loadFullCartItems = async (client, userId) => {
  const { data, error } = await client
    .from('cart_items')
    .select(`*, products (id, name, price, category)`)
    .eq('user_id', userId);
  if (error) {
    console.error('loadFullCartItems', error);
    return [];
  }
  return data || [];
};

window.syncStoreFromDB = async (client, userId) => {
  const cart = await window.loadCart(client, userId);
  window.populateStoreFromCart(cart);
};

window.populateStoreFromCart = (cartObj) => {
  Object.keys(window.Store.getCart()).forEach(k => window.Store.removeFromCart(k));
  Object.entries(cartObj || {}).forEach(([k, v]) => window.Store.addToCart(k, v || 0));
  window.Store.updateCartBadge();
};

window.computeCartTotals = (items, appliedPromo = null) => {
  let subtotal = 0;
  let count = 0;
  (items || []).forEach(item => {
    const p = item.products || {};
    const q = item.quantity || 0;
    subtotal += (p.price || 0) * q;
    count += q;
  });
  const discount = appliedPromo ? subtotal * appliedPromo.rate : 0;
  const shipping = subtotal > 0 ? (subtotal > 100 ? 0 : 9.90) : 0;
  const total = subtotal - discount + shipping;
  return { subtotal, count, discount, shipping, total, count };
};

// Shared review helpers (for item_detail and future)
window.loadReviews = async (client, productId) => {
  const { data, error } = await client
    .from('reviews')
    .select('*')
    .eq('product_id', productId)
    .order('created_at', { ascending: false });
  if (error) {
    console.error('loadReviews', error);
    return [];
  }
  return data || [];
};

window.addReviewDB = async (client, userId, productId, rating, comment) => {
  const { error } = await client.from('reviews').insert({
    user_id: userId,
    product_id: productId,
    rating,
    comment
  });
  if (error) console.error('addReviewDB', error);
  return !error;
};

// API items helpers
window.addApiItemDB = async (client, userId, title, description = '', category = 'general') => {
  const { error } = await client.from('api_items').insert({
    user_id: userId,
    title,
    description,
    category
  });
  if (error) console.error('addApiItemDB', error);
  return !error;
};

window.deleteApiItemDB = async (client, itemId) => {
  const { error } = await client.from('api_items').delete().eq('id', itemId);
  if (error) console.error('deleteApiItemDB', error);
  return !error;
};

window.addProductDB = async (client, name, description = '', price = 19.99, category = 'general') => {
  const { error } = await client.from('products').insert({
    name,
    description,
    price,
    category
  });
  if (error) console.error('addProductDB', error);
  return !error;
};

// --- Orders ---
window.loadOrders = async (client, userId) => {
  const { data, error } = await client
    .from('orders')
    .select(`
      id,
      order_number,
      total,
      status,
      created_at,
      order_items (
        quantity,
        price,
        products (id, name, category)
      )
    `)
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) {
    console.error('loadOrders', error);
    return [];
  }
  return (data || []).map(o => ({
    id: o.id,
    orderNumber: o.order_number,
    total: Number(o.total) || 0,
    status: o.status || 'completed',
    createdAt: o.created_at,
    items: (o.order_items || []).map(oi => ({
      productId: oi.product_id,
      name: oi.products?.name || 'Товар',
      category: oi.products?.category || '',
      quantity: oi.quantity,
      price: Number(oi.price) || 0
    }))
  }));
};
