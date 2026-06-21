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

  article.innerHTML = `
    <h2 data-testid="product-name-${product.id}">${product.name}</h2>
    <p class="price" data-testid="product-price-${product.id}">$${product.price.toFixed(2)}</p>
    <p class="description">${product.description || ''}</p>
    <a href="item_detail.html?id=${product.id}" 
       class="btn btn-secondary" 
       data-testid="product-view-${product.id}">View details</a>
  `;
  return article;
}

// Attach to window for use in non-module scripts (browser static site)
(window as any).createProductCard = createProductCard;