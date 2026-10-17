import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  const code = new URL(request.url).searchParams.get("code");
  if (!code) return NextResponse.redirect(new URL("/?error=missing_code", request.url));
  const supabase = await getSupabase();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  return NextResponse.redirect(new URL(error ? "/?error=auth" : "/dashboard", request.url));
}
