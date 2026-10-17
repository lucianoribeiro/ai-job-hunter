"use server";
import { getSupabase } from "@/lib/supabase";

export async function improveResume(form: FormData) {
  const supabase = await getSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error("Authentication required");
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY is not configured");
  const source = String(form.get("source") || "").slice(0,30000);
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      model: process.env.OPENAI_MODEL || "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: "Improve this resume for ATS readability. Return JSON with summary, experience, skills, education and warnings. Do not invent facts." },
        { role: "user", content: source }
      ]
    }),
    cache: "no-store"
  });
  if (!response.ok) throw new Error("AI service unavailable");
  return JSON.parse((await response.json()).choices[0].message.content);
}
