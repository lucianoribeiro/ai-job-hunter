import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  const searchParams=new URL(request.url).searchParams;
  const code = searchParams.get("code");
  if (!code) return NextResponse.redirect(new URL("/?error=missing_code", request.url));
  const supabase = await getSupabase();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  const requested=searchParams.get("next")||"/resumes";
  const target=new URL(requested,"https://internal.invalid");
  const allowedPath=/^\/(?:resumes|dashboard|applications\/outreach(?:\/[a-f0-9-]+\/compose)?)$/i.test(target.pathname);
  const allowedParams=[...target.searchParams.keys()].every(k=>["job","recipient","title","source","description"].includes(k));
  const next=requested.startsWith("/")&&!requested.startsWith("//")&&requested.length<=5500&&allowedPath&&allowedParams&&!target.hash?requested:"/resumes";
  return NextResponse.redirect(new URL(error ? "/?error=auth" : next, request.url));
}
