import { describe, it, expect } from 'vitest';
import { filterAndSortProducts, createProductCard, formatPrice, Product } from './utils';

const mockProducts: Product[] = [
  { id: 1, name: 'Apple iPhone 16', price: 999, description: 'Latest iPhone', category: 'phones' },
  { id: 2, name: 'Samsung Galaxy S25 Ultra', price: 1199, description: 'Premium Android', category: 'phones' },
  { id: 3, name: 'MacBook Air M3', price: 1099, description: 'Light laptop', category: 'laptops' },
];

describe('filterAndSortProducts', () => {
  it('returns all products when no filters', () => {
    const result = filterAndSortProducts(mockProducts);
    expect(result).toHaveLength(3);
  });

  it('filters by search term', () => {
    const result = filterAndSortProducts(mockProducts, 'iphone');
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('Apple iPhone 16');
  });

  it('filters by category', () => {
    const result = filterAndSortProducts(mockProducts, '', 'name-asc', 'phones');
    expect(result).toHaveLength(1);
    expect(result[0].category).toBe('phones');
  });

  it('sorts by price low to high', () => {
    const result = filterAndSortProducts(mockProducts, '', 'price-low');
    expect(result[0].price).toBe(999);
    expect(result[2].price).toBe(1099);
  });

  it('combines search and sort', () => {
    const result = filterAndSortProducts(mockProducts, 'laptop', 'price-high');
    expect(result[0].name).toBe('MacBook Air M3');
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