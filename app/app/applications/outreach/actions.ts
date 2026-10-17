"use server";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
function str(data:FormData,key:string,max:number){const v=data.get(key);if(typeof v!=="string"||v.length>max)throw new Error("Campo inválido");return v.trim()}
async function auth(){const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");return {supabase,user}}
export async function createOutreachDraft(form:FormData){
 const {supabase,user}=await auth();
 const opportunityId=str(form,"opportunity_id",40),recipient=str(form,"recipient",254).toLowerCase(),
 subject=str(form,"subject",250),body=str(form,"body",12000),resumeId=str(form,"resume_version_id",40);
 if(!/^[a-f0-9-]{36}$/i.test(opportunityId)||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient)||!subject||!body)
   throw new Error("Confira os dados da candidatura");
 const {data:job}=await supabase.from("opportunities").select("id").eq("id",opportunityId).eq("user_id",user.id).single();
 if(!job)throw new Error("Vaga não encontrada");
 let version:string|null=null;
 if(resumeId){
  if(!/^[a-f0-9-]{36}$/i.test(resumeId))throw new Error("Versão inválida");
  const {data}=await supabase.from("resume_versions").select("id,status").eq("id",resumeId).eq("user_id",user.id).single();
  if(!data||data.status!=="approved")throw new Error("Escolha uma versão de CV aprovada");
  version=data.id;
 }
 const {error}=await supabase.from("recruiter_drafts").insert({user_id:user.id,opportunity_id:job.id,
  resume_version_id:version,recipient_email:recipient,subject,body,status:"pending_review"});
 if(error)throw new Error("Não foi possível preparar o rascunho");
 redirect("/applications/outreach");
}
export async function approveOutreachDraft(form:FormData){
 const {supabase,user}=await auth();const id=str(form,"draft_id",40);
 if(!/^[a-f0-9-]{36}$/i.test(id))throw new Error("Rascunho inválido");
 const {error}=await supabase.from("recruiter_drafts").update({status:"approved"})
  .eq("id",id).eq("user_id",user.id).eq("status","pending_review");
 if(error)throw new Error("Não foi possível aprovar");
 redirect("/applications/outreach");
}
