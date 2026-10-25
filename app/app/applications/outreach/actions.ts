"use server";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {gmailAuthorization} from "@/lib/gmail-auth";
import {sendApprovedRecruiterEmail} from "./[id]/compose/actions";
function str(data:FormData,key:string,max:number){const v=data.get(key);if(typeof v!=="string"||v.length>max)throw new Error("Campo inválido");return v.trim()}
async function auth(){const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");return {supabase,user}}
export async function createOutreachDraft(form:FormData){
 const {supabase,user}=await auth();
 // The visible form is the user's final review. Require Gmail authorization
 // before creating a sendable database record.
 const {data:sessionInfo}=await supabase.auth.getSession();
 const canSend=(await gmailAuthorization(sessionInfo.session?.provider_token)).canSend;
 if(!canSend)throw new Error("Autorize o Gmail antes de clicar em Enviar candidatura.");
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
 // Reuse an unsent legacy review draft. Never issue another Gmail send for
 // an already sent, sending or externally drafted message.
 const {data:prior,error:priorError}=await supabase.from("recruiter_drafts")
  .select("id,status").eq("user_id",user.id).eq("opportunity_id",job.id)
  .eq("recipient_email",recipient).in("status",["pending_review","approved","drafted","sending","sent"])
  .order("created_at",{ascending:false}).limit(10);
 if(priorError)throw new Error("Não foi possível verificar candidaturas anteriores");
 const locked=prior?.find(d=>["drafted","sending","sent"].includes(d.status));
 if(locked)redirect("/applications/outreach?view=sent");
 const existing=prior?.[0];
 let draftId:string;
 if(existing){
  // Conditional update prevents reusing a draft concurrently claimed by a send.
  const {data:updated,error:updateError}=await supabase.from("recruiter_drafts")
   .update({subject,body,resume_file_id:fileId,resume_version_id:version,status:"approved"})
   .eq("id",existing.id).eq("user_id",user.id)
   .in("status",["pending_review","approved"]).select("id").maybeSingle();
  if(updateError||!updated)throw new Error("A candidatura mudou de status. Consulte o histórico antes de reenviar.");
  draftId=updated.id;
 }else{
  const {data:created,error:createError}=await supabase.from("recruiter_drafts")
   .insert({user_id:user.id,opportunity_id:job.id,resume_file_id:fileId,
    resume_version_id:version,recipient_email:recipient,subject,body,status:"approved"})
   .select("id").single();
  if(createError||!created)throw new Error("Não foi possível registrar a candidatura");
  draftId=created.id;
 }
 const sendForm=new FormData();sendForm.set("draft_id",draftId);sendForm.set("return_to","outreach");
 await sendApprovedRecruiterEmail(sendForm);
}
export async function approveOutreachDraft(form:FormData){
 const {supabase,user}=await auth();const id=str(form,"draft_id",40);
 if(!/^[a-f0-9-]{36}$/i.test(id))throw new Error("Rascunho inválido");
 const {error}=await supabase.from("recruiter_drafts").update({status:"approved"})
  .eq("id",id).eq("user_id",user.id).eq("status","pending_review");
 if(error)throw new Error("Não foi possível aprovar");
 redirect("/applications/outreach");
}
