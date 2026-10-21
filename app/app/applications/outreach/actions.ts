"use server";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
function str(data:FormData,key:string,max:number){const v=data.get(key);if(typeof v!=="string"||v.length>max)throw new Error("Campo inválido");return v.trim()}
async function auth(){const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");return {supabase,user}}
export async function createOutreachDraft(form:FormData){
 const {supabase,user}=await auth();
 const opportunityId=str(form,"opportunity_id",40),recipient=str(form,"recipient",254).toLowerCase(),
 subject=str(form,"subject",250),body=str(form,"body",12000),resumeId=str(form,"resume_version_id",40),
 listingUrl=str(form,"listing_url",2000),listingTitle=str(form,"listing_title",240),resumeFileId=str(form,"resume_file_id",40);
 if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient)||!subject||!body)
   throw new Error("Confira os dados da candidatura");
 let job:{id:string}|null=null;
 if(/^[a-f0-9-]{36}$/i.test(opportunityId))({data:job}=await supabase.from("opportunities").select("id").eq("id",opportunityId).eq("user_id",user.id).single());
 else if(opportunityId==="import"&&listingTitle&&/^https:\/\//i.test(listingUrl)){
  const {data:profile}=await supabase.from("career_profiles").select("id").eq("user_id",user.id).order("created_at").limit(1).single();
  if(!profile)throw new Error("Crie um perfil profissional antes de importar a publicação");
  const result=await supabase.from("opportunities").upsert({user_id:user.id,profile_id:profile.id,title:listingTitle,company:"A confirmar",listing_url:listingUrl,source:"Recruiter Monitor",work_mode:"unknown"},{onConflict:"user_id,listing_url"}).select("id").single();job=result.data;
 }
 if(!job)throw new Error("Vaga não encontrada");
 let version:string|null=null;
 if(resumeId){
  if(!/^[a-f0-9-]{36}$/i.test(resumeId))throw new Error("Versão inválida");
  const {data}=await supabase.from("resume_versions").select("id,status").eq("id",resumeId).eq("user_id",user.id).single();
  if(!data||data.status!=="approved")throw new Error("Escolha uma versão de CV aprovada");
  version=data.id;
 }
 let fileId:string|null=null;
 if(resumeFileId){
  if(!/^[a-f0-9-]{36}$/i.test(resumeFileId))throw new Error("PDF inválido");
  const {data:pdf}=await supabase.from("resume_files").select("id").eq("id",resumeFileId).eq("user_id",user.id).single();
  if(!pdf)throw new Error("PDF não pertence a este usuário");
  fileId=pdf.id;
 }
 if(!version&&!fileId) throw new Error("Selecione um CV para anexar.");
 const {data:prior}=await supabase.from("recruiter_drafts").select("id,status").eq("user_id",user.id).eq("opportunity_id",job.id).eq("recipient_email",recipient).in("status",["pending_review","approved","drafted"]).limit(1);
 if(prior?.length)throw new Error("Já existe uma candidatura para esta vaga e destinatário. Verifique o histórico antes de criar outra.");
 const {error}=await supabase.from("recruiter_drafts").insert({user_id:user.id,opportunity_id:job.id,resume_file_id:fileId,
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
