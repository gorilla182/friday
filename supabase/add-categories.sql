-- Add categories to products table for better filtering
-- Run in Supabase SQL Editor

ALTER TABLE public.products 
ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general';

-- Seed categories for existing products (adjust IDs as needed)
UPDATE public.products SET category = 'programming' WHERE id = 1; -- Python Handbook
UPDATE public.products SET category = 'testing' WHERE id = 2;     -- Playwright in Action
UPDATE public.products SET category = 'testing' WHERE id = 3;     -- API Testing Cookbook
UPDATE public.products SET category = 'testing' WHERE id = 4;     -- Test Data Builder
UPDATE public.products SET category = 'testing' WHERE id = 5;     -- Locators Guide

-- Optional: add more products with categories for testing
-- INSERT INTO public.products (name, description, price, category) VALUES ...