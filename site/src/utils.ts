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