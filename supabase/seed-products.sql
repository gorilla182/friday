-- Seed products with categories
-- Electronics catalog: phones, tablets, laptops
-- Run this in Supabase SQL Editor

-- =====================================================
-- SAFE CLEANUP: delete dependent tables FIRST (FK constraints)
-- =====================================================
DELETE FROM public.order_items;
DELETE FROM public.orders;           -- after order_items
DELETE FROM public.cart_items;

-- Delete reviews if the table exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'reviews'
    ) THEN
        DELETE FROM public.reviews;
    END IF;
END $$;

-- Delete api_items if you also want to clean user items (optional)
-- DELETE FROM public.api_items;

-- Now it is safe to delete products
DELETE FROM public.products;

INSERT INTO public.products (name, description, price, category) VALUES
  -- Phones (минимум 5)
  ('Apple iPhone 16', 'Latest iPhone with powerful A18 chip and excellent camera.', 999.00, 'phones'),
  ('Samsung Galaxy S25 Ultra', 'Premium flagship with S Pen and top-tier display.', 1199.00, 'phones'),
  ('Google Pixel 9 Pro', 'Best-in-class camera and clean Android experience.', 899.00, 'phones'),
  ('OnePlus 13', 'Blazing fast performance and rapid charging.', 799.00, 'phones'),
  ('Xiaomi 15 Pro', 'High-end specs at competitive price.', 699.00, 'phones'),

  -- Tablets (минимум 5)
  ('Apple iPad Pro 13"', 'M4 chip, stunning Liquid Retina XDR display.', 1299.00, 'tablets'),
  ('Samsung Galaxy Tab S10+', 'Large vibrant AMOLED screen for media and work.', 1099.00, 'tablets'),
  ('Lenovo Tab P12 Pro', 'Great for drawing, reading and entertainment.', 649.00, 'tablets'),
  ('Microsoft Surface Pro 11', 'Windows 11 tablet with excellent keyboard support.', 999.00, 'tablets'),
  ('Huawei MatePad Pro 12.2', 'Premium build quality and stylus precision.', 749.00, 'tablets'),

  -- Laptops (минимум 5)
  ('Apple MacBook Air M3 13"', 'Lightweight, powerful and long battery life.', 1099.00, 'laptops'),
  ('Dell XPS 14', 'Premium ultrabook with gorgeous InfinityEdge display.', 1399.00, 'laptops'),
  ('Lenovo ThinkPad X1 Carbon', 'Business laptop with legendary keyboard.', 1599.00, 'laptops'),
  ('HP Spectre x360 14"', 'Versatile 2-in-1 convertible laptop.', 1199.00, 'laptops'),
  ('ASUS Zenbook 14 OLED', 'Stunning OLED display and premium aluminum body.', 949.00, 'laptops')
ON CONFLICT (id) DO NOTHING;

-- To fully reset and reseed:
-- TRUNCATE public.products RESTART IDENTITY CASCADE;
-- Then run the INSERT above.