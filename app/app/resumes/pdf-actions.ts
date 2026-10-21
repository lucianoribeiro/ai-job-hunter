"use server";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { getSupabase } from "@/lib/supabase";

const BUCKET = "private-resumes";
const MAX_BYTES = 5 * 1024 * 1024;
function validLanguage(value: unknown): value is "en-US" | "pt-BR" {
 return value === "en-US" || value === "pt-BR";
}
export async function uploadResumePdf(form: FormData) {
 const supabase = await getSupabase();
 const { data: {user}, error: authError } = await supabase.auth.getUser();
 if(authError || !user) redirect("/");
 const file = form.get("file");
 const language = form.get("language");
 if(!(file instanceof File) || !validLanguage(language)) throw new Error("Selecione um PDF e um idioma válido.");
 if(file.size < 1 || file.size > MAX_BYTES || file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf"))
   throw new Error("Somente PDF de até 5 MB é permitido.");
 const bytes = new Uint8Array(await file.arrayBuffer());
 if(new TextDecoder("ascii").decode(bytes.slice(0,5)) !== "%PDF-") throw new Error("O arquivo não é um PDF válido.");
 const {data:old,error:lookupError} = await supabase.from("resume_files").select("id,object_path").eq("user_id",user.id).eq("language",language).maybeSingle();
 if(lookupError) throw new Error("Falha ao consultar os currículos existentes.");
 // Immutable objects prevent replacing the previous PDF before the DB operation succeeds.
 const key = user.id + "/" + crypto.randomUUID() + ".pdf";
 const {error:uploadError} = await supabase.storage.from(BUCKET).upload(key,bytes,{contentType:"application/pdf",upsert:false,cacheControl:"private, no-store"});
 if(uploadError) throw new Error("Falha ao guardar o PDF privado. Verifique se a migração Supabase foi executada.");
 const metadata = {user_id:user.id,language,label:language === "en-US" ? "Executive Resume – English" : "Currículo Executivo – Português",object_path:key,original_name:file.name.slice(0,180),bytes:file.size};
 const save = old
   ? await supabase.from("resume_files").update(metadata).eq("id",old.id).eq("user_id",user.id)
   : await supabase.from("resume_files").insert(metadata);
 if(save.error) {
   await supabase.storage.from(BUCKET).remove([key]);
   throw new Error("Falha ao registrar o currículo.");
 }
 if(old?.object_path) await supabase.storage.from(BUCKET).remove([old.object_path]);
 revalidatePath("/resumes");
 redirect("/resumes");
}
export async function deleteResumePdf(form: FormData) {
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();
 if(!user) redirect("/");
 const id=String(form.get("id")||"");
 if(!/^[0-9a-f-]{36}$/i.test(id)) throw new Error("ID inválido.");
 const {data:record,error}=await supabase.from("resume_files").select("object_path").eq("id",id).eq("user_id",user.id).single();
 if(error||!record) throw new Error("Currículo não encontrado.");
 const deletion=await supabase.storage.from(BUCKET).remove([record.object_path]);
 if(deletion.error) throw new Error("Falha ao apagar o arquivo.");
 const result=await supabase.from("resume_files").delete().eq("id",id).eq("user_id",user.id);
 if(result.error) throw new Error("Falha ao atualizar registro do arquivo.");
 revalidatePath("/resumes");
 redirect("/resumes");
}
