// Pure functions for unit testing

export interface Product {
  id: number;
  name: string;
  description?: string;
  price: number;
  category?: string;
}

export function filterAndSortProducts(
  products: Product[],
  searchTerm: string = '',
  sortValue: string = 'name-asc',
  categoryFilter: string = ''
): Product[] {
  let filtered = [...products];

  // Search by name or description
  if (searchTerm.trim()) {
    const term = searchTerm.toLowerCase().trim();
    filtered = filtered.filter(p =>
      p.name.toLowerCase().includes(term) ||
      (p.description && p.description.toLowerCase().includes(term))
    );
  }

  // Category filter
  if (categoryFilter) {
    filtered = filtered.filter(p => p.category === categoryFilter);
  }

  // Sort
  switch (sortValue) {
    case 'name-asc':
      filtered.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'name-desc':
      filtered.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case 'price-low':
      filtered.sort((a, b) => a.price - b.price);
      break;
    case 'price-high':
      filtered.sort((a, b) => b.price - a.price);
      break;
  }

  return filtered;
}

export function createProductCard(product: Product): HTMLElement {
  const article = document.createElement('article');
  article.className = 'product-card';
  article.setAttribute('data-testid', `product-card-${product.id}`);
  article.setAttribute('data-product-id', String(product.id));
  article.setAttribute('data-stock', '1');

  const cat = product.category || 'general';
  const pid = product.id;

  article.innerHTML = `
    <span class="test-tag product-id-tag" data-testid="product-id-tag">${pid}</span>
    <div class="product-thumb" data-testid="product-thumb-${pid}">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <path d="M8 12h8M12 8v8"/>
      </svg>
    </div>
    <div>
      <span class="product-category" data-testid="product-category-${pid}">${cat}</span>
      <div class="product-name" data-testid="product-name-${pid}">${product.name}</div>
    </div>
    <div class="product-meta-row">
      <span class="product-price" data-testid="product-price-${pid}">${formatPrice(product.price)}</span>
      <span class="product-rating"><svg width="12" height="12" viewBox="0 0 24 24"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/></svg>4.5</span>
    </div>
    <div class="product-card-actions">
      <button type="button" class="btn btn-primary btn-block" data-action="add-to-cart" data-product-id="${pid}" data-testid="add-to-cart-button">Добавить в корзину</button>
    </div>
    <button type="button" class="btn btn-ghost btn-sm" style="margin-top:4px;width:100%" data-action="review" data-product-id="${pid}" data-testid="leave-review-${pid}">Оставить отзыв</button>
  `;
  return article;
}

export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`;
}

// Attach to window for use in non-module scripts (browser static site)
(window as any).createProductCard = createProductCard;
(window as any).filterAndSortProducts = filterAndSortProducts;
(window as any).formatPrice = formatPrice;