"use server";
import { redirect } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import { extractResume } from "@/lib/resume-import";

export type ImportState = { text: string; error: string; warnings: string[]; filename: string };
export async function previewImport(_state: ImportState, data: FormData): Promise<ImportState> {
  const supabase = await getSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/");
  const file = data.get("resume");
  if (!(file instanceof File)) return { text: "", error: "Selecione um PDF ou DOCX.", warnings: [], filename: "" };
  try {
    const result = await extractResume(file);
    // File bytes and extracted content are not persisted by this action.
    return { text: result.extractedText, error: "", warnings: result.warnings, filename: file.name.slice(0, 150) };
  } catch (error) {
    return { text: "", error: error instanceof Error ? error.message : "Falha na leitura do arquivo.", warnings: [], filename: "" };
  }
}
