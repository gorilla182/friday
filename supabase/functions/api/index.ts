// supabase/functions/api/index.ts
// Realistic API layer for teststand (behaves like real backend APIs)
// Base URL: https://<project>.supabase.co/functions/v1/api
// Endpoints mimic common patterns in real apps.

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
const anonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const json = (data: any, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });

const error = (message: string, code: string, status = 400) =>
  json({ error: message, code }, status);

serve(async (req: Request) => {
  const url = new URL(req.url);
  const path = url.pathname.replace(/^\/api/, ""); // normalize
  const method = req.method;

  // Public + anon client
  const supabase = createClient(supabaseUrl, anonKey);

  // Client with auth header (for protected routes)
  const authHeader = req.headers.get("Authorization") || "";
  const authedClient = createClient(supabaseUrl, anonKey, {
    global: { headers: { Authorization: authHeader } },
  });

  // Service role for admin
  const adminClient = createClient(supabaseUrl, serviceRoleKey);

  try {
    // ============ AUTH ============
    if (path === "/auth/register" && method === "POST") {
      const body = await req.json();
      const { email, password, name } = body;

      if (!email || !password || !name) {
        return error("Email, password and name are required", "validation_error", 422);
      }

      const { data, error: err } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { name } },
      });

      if (err) return error(err.message, "auth_error", 400);
      return json({ id: data.user?.id, email, name }, 201);
    }

    if (path === "/auth/login" && method === "POST") {
      const body = await req.json();
      const { email, password } = body;

      const { data, error: err } = await supabase.auth.signInWithPassword({ email, password });

      if (err) return error("Invalid credentials", "invalid_credentials", 401);

      return json({
        access_token: data.session?.access_token,
        token_type: "Bearer",
        user: data.user,
      });
    }

    // ============ ITEMS ============
    if (path === "/items" && method === "GET") {
      const page = parseInt(url.searchParams.get("page") || "1");
      const limit = Math.min(parseInt(url.searchParams.get("limit") || "10"), 100);
      const category = url.searchParams.get("category");

      let query = supabase
        .from("api_items")
        .select("id, title, description, category, user_id, created_at", { count: "exact" })
        .order("created_at", { ascending: false });

      if (category) query = query.eq("category", category);

      const from = (page - 1) * limit;
      const to = from + limit - 1;
      query = query.range(from, to);

      const { data, error: err, count } = await query;

      if (err) return error(err.message, "db_error", 500);

      return json({
        items: data,
        page,
        limit,
        total: count,
        total_pages: Math.ceil((count || 0) / limit),
      });
    }

    if (path === "/items" && method === "POST") {
      const body = await req.json();
      const { title, description = "", category = "general" } = body;

      if (!title) return error("Title is required", "validation_error", 422);

      const { data: userData } = await authedClient.auth.getUser();
      if (!userData.user) return error("Authentication required", "unauthorized", 401);

      const { data, error: err } = await authedClient
        .from("api_items")
        .insert({
          title,
          description,
          category,
          user_id: userData.user.id,
        })
        .select()
        .single();

      if (err) return error(err.message, "db_error", 500);
      return json(data, 201);
    }

    // Dynamic /items/:id
    const itemMatch = path.match(/^\/items\/(\d+)$/);
    if (itemMatch) {
      const id = parseInt(itemMatch[1]);

      if (method === "GET") {
        const { data, error: err } = await supabase
          .from("api_items")
          .select("*")
          .eq("id", id)
          .single();

        if (err || !data) return error("Item not found", "not_found", 404);
        return json(data);
      }

      if (method === "PUT") {
        const body = await req.json();
        const { data: userData } = await authedClient.auth.getUser();
        if (!userData.user) return error("Authentication required", "unauthorized", 401);

        const { data: existing } = await authedClient
          .from("api_items")
          .select("user_id")
          .eq("id", id)
          .single();

        if (!existing) return error("Item not found", "not_found", 404);
        if (existing.user_id !== userData.user.id) {
          return error("You can only update your own items", "forbidden", 403);
        }

        const { data, error: err } = await authedClient
          .from("api_items")
          .update({
            title: body.title,
            description: body.description,
            category: body.category,
          })
          .eq("id", id)
          .select()
          .single();

        if (err) return error(err.message, "db_error", 500);
        return json(data);
      }

      if (method === "DELETE") {
        const { data: userData } = await authedClient.auth.getUser();
        if (!userData.user) return error("Authentication required", "unauthorized", 401);

        const { data: existing } = await authedClient
          .from("api_items")
          .select("user_id")
          .eq("id", id)
          .single();

        if (!existing) return error("Item not found", "not_found", 404);
        if (existing.user_id !== userData.user.id) {
          return error("You can only delete your own items", "forbidden", 403);
        }

        const { error: err } = await authedClient.from("api_items").delete().eq("id", id);
        if (err) return error(err.message, "db_error", 500);
        return new Response(null, { status: 204 });
      }
    }

    // ============ TRIGGER ERROR (for testing error handling) ============
    if (path === "/items/trigger-error" && method === "POST") {
      const body = await req.json();
      const payload = body.payload || "";

      if (payload === "server_error") {
        return error("Simulated internal server error", "server_error", 500);
      }

      if (payload === "rate_limit") {
        return error("Rate limit exceeded. Try again later.", "rate_limit_exceeded", 429);
      }

      // Stable success for other cases (no random/flaky behavior)
      return json({ status: "ok", message: "Request accepted." });
    }

    // ============ ADMIN RESET (for test isolation) ============
    if (path === "/admin/reset" && method === "POST") {
      // In real apps this would be heavily protected (API key, IP allowlist, etc.)
      const { data, error: err } = await adminClient.rpc("reset_teststand");

      if (err) return error(err.message, "reset_failed", 500);
      return json(data || { status: "ok", message: "Database has been reset to initial state." });
    }

    // ============ CATEGORIES (for filters) ============
    if (path === "/categories" && method === "GET") {
      const { data, error: err } = await supabase
        .from("api_items")
        .select("category")
        .not("category", "is", null);

      if (err) return error(err.message, "db_error", 500);

      const unique = [...new Set(data.map(d => d.category))];
      return json(unique);
    }

    // ============ PRODUCTS (shop mirror for API testing) ============
    if (path === "/products" && method === "GET") {
      const { data, error: err } = await supabase
        .from("products")
        .select("*")
        .order("id");

      if (err) return error(err.message, "db_error", 500);
      return json(data);
    }

    // ============ REVIEWS (new UI coverage) ============
    if (path === "/reviews" && method === "GET") {
      const productId = url.searchParams.get("product_id");
      let query = supabase.from("reviews").select("id, product_id, user_id, rating, comment, created_at");

      if (productId) {
        query = query.eq("product_id", productId);
      }

      const { data, error: err } = await query.order("created_at", { ascending: false });
      if (err) return error(err.message, "db_error", 500);
      return json(data);
    }

    if (path === "/reviews" && method === "POST") {
      const body = await req.json();
      const { product_id, rating, comment = "" } = body;

      if (!product_id || !rating || rating < 1 || rating > 5) {
        return error("product_id and rating (1-5) are required", "validation_error", 422);
      }

      const { data: userData } = await authedClient.auth.getUser();
      if (!userData.user) return error("Authentication required", "unauthorized", 401);

      const { data, error: err } = await authedClient
        .from("reviews")
        .insert({
          product_id,
          user_id: userData.user.id,
          rating,
          comment,
        })
        .select()
        .single();

      if (err) return error(err.message, "db_error", 500);
      return json(data, 201);
    }

    return error("Not found", "not_found", 404);
  } catch (e) {
    console.error(e);
    return error("Internal server error", "internal_error", 500);
  }
});