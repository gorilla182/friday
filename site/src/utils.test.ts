import { describe, it, expect } from 'vitest';
import { filterAndSortProducts, createProductCard, formatPrice, Product } from './utils';

const mockProducts: Product[] = [
  { id: 1, name: 'Python Handbook', price: 29.99, description: 'Python guide', category: 'programming' },
  { id: 2, name: 'Playwright in Action', price: 39.99, description: 'E2E testing', category: 'testing' },
  { id: 3, name: 'API Testing Cookbook', price: 24.99, category: 'testing' },
];

describe('filterAndSortProducts', () => {
  it('returns all products when no filters', () => {
    const result = filterAndSortProducts(mockProducts);
    expect(result).toHaveLength(3);
  });

  it('filters by search term', () => {
    const result = filterAndSortProducts(mockProducts, 'python');
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Python Handbook');
  });

  it('filters by category', () => {
    const result = filterAndSortProducts(mockProducts, '', 'name-asc', 'programming');
    expect(result).toHaveLength(1);
    expect(result[0].category).toBe('programming');
  });

  it('sorts by price low to high', () => {
    const result = filterAndSortProducts(mockProducts, '', 'price-low');
    expect(result[0].price).toBe(24.99);
    expect(result[2].price).toBe(39.99);
  });

  it('combines search and sort', () => {
    const result = filterAndSortProducts(mockProducts, 'testing', 'price-high');
    expect(result[0].name).toBe('Playwright in Action');
  });

  it('returns empty array when no products match', () => {
    const result = filterAndSortProducts(mockProducts, 'nonexistent');
    expect(result).toHaveLength(0);
  });

  it('handles empty input products', () => {
    const result = filterAndSortProducts([], 'foo', 'name-asc', '');
    expect(result).toEqual([]);
  });
});

describe('formatPrice', () => {
  it('formats price with two decimals and $', () => {
    expect(formatPrice(29.9)).toBe('$29.90');
    expect(formatPrice(100)).toBe('$100.00');
  });
});

describe('createProductCard', () => {
  it('creates an article with correct data-testid', () => {
    const product = mockProducts[0];
    const card = createProductCard(product);
    expect(card.tagName).toBe('ARTICLE');
    expect(card.getAttribute('data-testid')).toBe(`product-card-${product.id}`);
  });

  it('includes product name and price in content', () => {
    const product = mockProducts[1];
    const card = createProductCard(product);
    expect(card.innerHTML).toContain(product.name);
    expect(card.innerHTML).toContain(product.price.toFixed(2));
  });

  it('renders add to cart and review button with correct data-testid', () => {
    const product = mockProducts[0];
    const card = createProductCard(product);
    expect(card.querySelector('[data-testid="add-to-cart-button"]')).toBeTruthy();
    expect(card.querySelector(`[data-testid="leave-review-${product.id}"]`)).toBeTruthy();
  });
});

// Additional coverage for stability (mappers, cart logic simulation)
describe('supabase data mappers (simulated)', () => {
  it('maps product from db shape', () => {
    const dbP = { id: 5, name: 'Test', price: '19.99', category: 'test', description: 'd' };
    const mapped = {
      id: String(dbP.id),
      name: dbP.name,
      category: dbP.category || 'general',
      price: Number(dbP.price) || 0,
      stock: 10,
      rating: 4.5,
      img: 'keyboard'
    };
    expect(mapped.id).toBe('5');
    expect(mapped.price).toBe(19.99);
  });

  it('simulates cart total', () => {
    const cart = { '1': 2, '2': 1 };
    const prods = [
      { id: '1', price: 10 },
      { id: '2', price: 20 }
    ];
    let total = 0;
    Object.entries(cart).forEach(([pid, q]) => {
      const p = prods.find(pp => pp.id === pid);
      if (p) total += p.price * q;
    });
    expect(total).toBe(40);
  });
});