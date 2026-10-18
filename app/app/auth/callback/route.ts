import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  const searchParams=new URL(request.url).searchParams;
  const code = searchParams.get("code");
  if (!code) return NextResponse.redirect(new URL("/?error=missing_code", request.url));
  const supabase = await getSupabase();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  const requested=searchParams.get("next")||"/dashboard";
  const next=/^\/(?:dashboard|applications\/outreach(?:\/[a-f0-9-]+\/compose)?)$/i.test(requested)?requested:"/dashboard";
  return NextResponse.redirect(new URL(error ? "/?error=auth" : next, request.url));
}
