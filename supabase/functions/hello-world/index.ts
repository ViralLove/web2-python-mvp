import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req) => {
  const { name } = await req.json();
  return new Response(JSON.stringify({ message: `Hello, ${name}!` }), {
    headers: { "Content-Type": "application/json" },
  });
});
