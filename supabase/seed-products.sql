-- Seed products with categories
-- Run this in Supabase SQL Editor

INSERT INTO public.products (name, description, price, category) VALUES
  ('Python Handbook', 'A concise guide to Python programming.', 29.99, 'programming'),
  ('Playwright in Action', 'End-to-end testing with Playwright.', 39.99, 'testing'),
  ('API Testing Cookbook', 'Recipes for REST API test automation.', 24.99, 'testing'),
  ('Test Data Builder', 'Patterns for predictable test fixtures.', 19.99, 'testing'),
  ('Locators Guide', 'Stable selectors for UI automation.', 14.99, 'testing')
ON CONFLICT (id) DO NOTHING;

-- If you want to reset products, you can truncate first if needed:
-- TRUNCATE public.products RESTART IDENTITY CASCADE;