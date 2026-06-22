-- =====================================================
-- Teststand Reset Function (run with SERVICE ROLE)
-- =====================================================
-- This mimics the old /admin/reset endpoint.
-- IMPORTANT: Run this using the SERVICE_ROLE key (not anon/publishable).

create or replace function public.reset_teststand()
returns json
language plpgsql
security definer
set search_path = public
as $$
declare
  alice_id uuid;
begin
  -- Delete all app data (but keep auth users)
  delete from public.order_items;
  delete from public.orders;
  delete from public.cart_items;
  delete from public.api_items;
  delete from public.products;

  -- Re-seed products (electronics catalog)
  insert into public.products (name, description, price, category) values
    -- Phones
    ('Apple iPhone 16', 'Latest iPhone with powerful A18 chip and excellent camera.', 999.00, 'phones'),
    ('Samsung Galaxy S25 Ultra', 'Premium flagship with S Pen and top-tier display.', 1199.00, 'phones'),
    ('Google Pixel 9 Pro', 'Best-in-class camera and clean Android experience.', 899.00, 'phones'),
    ('OnePlus 13', 'Blazing fast performance and rapid charging.', 799.00, 'phones'),
    ('Xiaomi 15 Pro', 'High-end specs at competitive price.', 699.00, 'phones'),

    -- Tablets
    ('Apple iPad Pro 13"', 'M4 chip, stunning Liquid Retina XDR display.', 1299.00, 'tablets'),
    ('Samsung Galaxy Tab S10+', 'Large vibrant AMOLED screen for media and work.', 1099.00, 'tablets'),
    ('Lenovo Tab P12 Pro', 'Great for drawing, reading and entertainment.', 649.00, 'tablets'),
    ('Microsoft Surface Pro 11', 'Windows 11 tablet with excellent keyboard support.', 999.00, 'tablets'),
    ('Huawei MatePad Pro 12.2', 'Premium build quality and stylus precision.', 749.00, 'tablets'),

    -- Laptops
    ('Apple MacBook Air M3 13"', 'Lightweight, powerful and long battery life.', 1099.00, 'laptops'),
    ('Dell XPS 14', 'Premium ultrabook with gorgeous InfinityEdge display.', 1399.00, 'laptops'),
    ('Lenovo ThinkPad X1 Carbon', 'Business laptop with legendary keyboard.', 1599.00, 'laptops'),
    ('HP Spectre x360 14"', 'Versatile 2-in-1 convertible laptop.', 1199.00, 'laptops'),
    ('ASUS Zenbook 14 OLED', 'Stunning OLED display and premium aluminum body.', 949.00, 'laptops');

  -- Find alice
  select id into alice_id from auth.users where email = 'alice@example.com' limit 1;

  if alice_id is not null then
    -- Re-seed api_items owned by alice
    insert into public.api_items (title, description, category, user_id) values
      ('Write login tests', 'Cover happy path and invalid credentials.', 'testing', alice_id),
      ('Practice pagination', 'Assert page boundaries and filters.', 'api', alice_id),
      ('Handle 401 responses', 'Verify unauthorized access is blocked.', 'api', alice_id);
  end if;

  return json_build_object(
    'status', 'ok',
    'message', 'Database has been reset to initial state.',
    'alice_id', alice_id
  );
end;
$$;

-- Grant execute so that Edge Function / service role can call it
grant execute on function public.reset_teststand() to service_role;
grant execute on function public.reset_teststand() to authenticated;  -- optional, if you want to expose via RPC with auth
