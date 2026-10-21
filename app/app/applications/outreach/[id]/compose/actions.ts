"use server";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {createGmailDraft,gmailDraftMime} from "@/lib/gmail-api";
import {professionalResumePdf,safeResumeFilename} from "@/lib/resume-pdf";

export async function createApprovedGmailDraft(form:FormData){
 const id=String(form.get("draft_id")||"");if(!/^[a-f0-9-]{36}$/i.test(id))throw new Error("Invalid draft");
 const supabase=await getSupabase();const [{data:{user}},{data:sessionData}]=await Promise.all([supabase.auth.getUser(),supabase.auth.getSession()]);
 if(!user)redirect("/");const token=sessionData.session?.provider_token;if(!token)redirect(`/applications/outreach/${id}/compose?gmail=connect`);
 const {data:draft}=await supabase.from("recruiter_drafts").select("id,recipient_email,subject,body,status,resume_version_id,resume_file_id").eq("id",id).eq("user_id",user.id).single();
 if(!draft||draft.status!=="approved"||(!draft.resume_version_id&&!draft.resume_file_id))throw new Error("Approved draft and resume required");
 let pdf:Uint8Array,filename:string;
 if(draft.resume_file_id){
  const {data:file}=await supabase.from("resume_files").select("object_path,language").eq("id",draft.resume_file_id).eq("user_id",user.id).single();
  if(!file)throw new Error("Private resume not found");
  const {data:blob,error:storageError}=await supabase.storage.from("private-resumes").download(file.object_path);
  if(storageError||!blob)throw new Error("Could not download private CV");
  pdf=new Uint8Array(await blob.arrayBuffer());
  filename=file.language==="en-US"?"Luciano_Ribeiro_Resume_EN.pdf":"Luciano_Ribeiro_Curriculo_PTBR.pdf";
 }else{
  const {data:version}=await supabase.from("resume_versions").select("content,status,target_role,label").eq("id",draft.resume_version_id).eq("user_id",user.id).single();
  if(!version||version.status!=="approved")throw new Error("Approved resume required");
  const role=version.target_role||version.label||"Professional Resume";
  pdf=await professionalResumePdf(version.content,role);
  filename=safeResumeFilename(role);
 }
 const gmail=await createGmailDraft(token,gmailDraftMime({to:draft.recipient_email,subject:draft.subject,body:draft.body,filename,pdf}));
 const {error}=await supabase.from("recruiter_drafts").update({status:"drafted",gmail_draft_id:gmail.id,gmail_created_at:new Date().toISOString()}).eq("id",id).eq("user_id",user.id).eq("status","approved");
 if(error)throw new Error("Gmail draft created but local status could not be updated");
 redirect(`/applications/outreach/${id}/compose?gmail=created`);
}
