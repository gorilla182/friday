-- Ensure category column (run if schema is old)
ALTER TABLE public.products 
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general';

-- Note: Current catalog seeded in seed-products.sql / reset_teststand()
-- Categories: phones, tablets, laptops