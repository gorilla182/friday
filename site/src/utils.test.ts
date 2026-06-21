import { describe, it, expect } from 'vitest';
import { filterAndSortProducts, Product } from './utils';

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
});