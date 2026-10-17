"use server";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { getSupabase } from "@/lib/supabase";

async function authenticated() {
 const supabase=await getSupabase();
 const {data:{user},error}=await supabase.auth.getUser();
 if(error||!user) redirect("/");
 return {supabase,user};
}
function field(form:FormData,key:string,limit:number) {
 const value=form.get(key);
 if(typeof value!=="string") throw new Error("Invalid field: "+key);
 if(value.length>limit) throw new Error("Field is too long: "+key);
 return value.trim();
}
export async function createResume(form:FormData) {
 const {supabase,user}=await authenticated();
 const title=field(form,"title",120),language=field(form,"language",10);
 if(!title||!["pt-BR","en-US"].includes(language)) throw new Error("Invalid resume");
 const {error}=await supabase.from("resumes").insert({
  user_id:user.id,title,language,summary:field(form,"summary",12000),
  experience:field(form,"experience",60000),skills:field(form,"skills",12000),
  education:field(form,"education",12000),source:"manual"
 });
 if(error) throw new Error("Unable to save resume");
 revalidatePath("/resumes");
 redirect("/resumes");
}
export async function createVersion(form:FormData) {
 const {supabase,user}=await authenticated();
 const resumeId=field(form,"resume_id",50), label=field(form,"label",120);
 const targetRole=field(form,"target_role",120),content=field(form,"content",80000);
 if(!/^[0-9a-f-]{36}$/i.test(resumeId)||!label||!content) throw new Error("Invalid version");
 const {data:resume,error:lookupError}=await supabase.from("resumes")
  .select("id").eq("id",resumeId).eq("user_id",user.id).single();
 if(lookupError||!resume) throw new Error("Resume does not belong to this account");
 const {error}=await supabase.from("resume_versions").insert({
  user_id:user.id,resume_id:resumeId,label,target_role:targetRole,content,status:"draft"
 });
 if(error) throw new Error("Unable to save version");
 revalidatePath("/resumes");
 redirect("/resumes");
}
export async function approveVersion(form:FormData) {
 const {supabase,user}=await authenticated();
 const id=field(form,"version_id",50);
 if(!/^[0-9a-f-]{36}$/i.test(id)) throw new Error("Invalid version identifier");
 const {error}=await supabase.from("resume_versions").update({status:"approved"})
   .eq("id",id).eq("user_id",user.id);
 if(error) throw new Error("Unable to approve version");
 revalidatePath("/resumes");
 redirect("/resumes");
}
