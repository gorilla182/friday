-- Ensure category column exists (for electronics catalog)
-- Run in Supabase SQL Editor if needed

ALTER TABLE public.products 
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general';

-- The main catalog is seeded via seed-products.sql or reset_teststand()
-- Categories used: phones, tablets, laptops

-- To clean and reseed fresh electronics catalog, use:
-- DELETE FROM public.products;
-- Then INSERT the new products (see seed-products.sql)