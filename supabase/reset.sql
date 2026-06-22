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

  -- Re-seed products
  insert into public.products (name, description, price, category) values
    ('Python Handbook', 'A concise guide to Python programming.', 29.99, 'programming'),
    ('Playwright in Action', 'End-to-end testing with Playwright.', 39.99, 'testing'),
    ('API Testing Cookbook', 'Recipes for REST API test automation.', 24.99, 'testing'),
    ('Test Data Builder', 'Patterns for predictable test fixtures.', 19.99, 'testing'),
    ('Locators Guide', 'Stable selectors for UI automation.', 14.99, 'testing');

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
