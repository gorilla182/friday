-- Seed initial api_items for alice (run AFTER creating the user in Supabase Auth)

INSERT INTO public.api_items (title, description, category, user_id)
SELECT 'Write login tests', 'Cover happy path and invalid credentials.', 'testing', id
FROM auth.users 
WHERE email = 'alice@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO public.api_items (title, description, category, user_id)
SELECT 'Practice pagination', 'Assert page boundaries and filters.', 'api', id
FROM auth.users 
WHERE email = 'alice@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO public.api_items (title, description, category, user_id)
SELECT 'Handle 401 responses', 'Verify unauthorized access is blocked.', 'api', id
FROM auth.users 
WHERE email = 'alice@example.com'
ON CONFLICT DO NOTHING;
