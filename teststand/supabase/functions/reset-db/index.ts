// supabase/functions/reset-db/index.ts
// Deploy with: supabase functions deploy reset-db
// Call: POST https://<project>.supabase.co/functions/v1/reset-db

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

serve(async (req: Request) => {
  // Only allow POST requests (like the original API)
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

    if (!serviceRoleKey) {
      return Response.json(
        { error: "Service role key not configured" },
        { status: 500 }
      );
    }

    const supabase = createClient(supabaseUrl, serviceRoleKey, {
      auth: { persistSession: false },
    });

    // Call our reset function
    const { data, error } = await supabase.rpc("reset_teststand");

    if (error) {
      console.error("Reset error:", error);
      return Response.json(
        { error: error.message, code: "reset_failed" },
        { status: 500 }
      );
    }

    return Response.json(data ?? { status: "ok", message: "Database has been reset." });
  } catch (err) {
    console.error(err);
    return Response.json(
      { error: "Internal server error", code: "internal_error" },
      { status: 500 }
    );
  }
});
