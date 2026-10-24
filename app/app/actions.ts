"use server";
import { redirect } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import { applicationOrigin } from "@/lib/application-origin";

export async function signIn() {
  const supabase = await getSupabase();
  const siteUrl = applicationOrigin();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: new URL("/auth/callback", siteUrl).toString() }
  });
  if (error || !data.url) throw new Error("Unable to initiate Google login");
  redirect(data.url);
}

export async function connectGmail(form:FormData) {
  const supabase=await getSupabase(),siteUrl=applicationOrigin();
  const next=String(form.get("next")||"/applications/outreach");
  const safeNext=/^\/applications\/outreach(?:\/[a-f0-9-]+\/compose)?$/i.test(next)?next:"/applications/outreach";
  const callback=new URL("/auth/callback",siteUrl);callback.searchParams.set("next",safeNext);
  const {data,error}=await supabase.auth.signInWithOAuth({provider:"google",options:{redirectTo:callback.toString(),scopes:"https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/gmail.send",queryParams:{access_type:"offline",prompt:"consent",include_granted_scopes:"true"}}});
  if(error||!data.url)throw new Error("Unable to initiate Gmail authorization");
  redirect(data.url);
}

export async function signOut() {
  const supabase = await getSupabase();
  await supabase.auth.signOut();
  redirect("/");
}

export async function createCareerProfile(form: FormData) {
  const supabase = await getSupabase();
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) redirect("/");
  const label = String(form.get("label") || "").trim().slice(0, 120);
  const industry = String(form.get("industry") || "").trim().slice(0, 120);
  const roles = String(form.get("roles") || "").split(",").map(s => s.trim()).filter(Boolean).slice(0, 20);
  const city = String(form.get("city") || "").trim().slice(0, 120);
  const radius = Number(form.get("radius") || 50);
  if (!label || !roles.length || !Number.isInteger(radius) || radius < 0 || radius > 500)
    throw new Error("Enter a profile name, target roles and a valid radius");
  const { error: insertError } = await supabase.from("career_profiles").insert({
    user_id: user.id, label, industry, target_roles: roles, origin_city: city,
    remote_first: true, include_hybrid: form.get("hybrid") === "on", max_radius_km: radius
  });
  if (insertError) throw new Error("Could not save career profile");
  redirect("/dashboard");
}
