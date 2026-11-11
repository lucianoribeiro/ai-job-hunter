"use server";
import { redirect } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
export async function saveJob(form:FormData){
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const profileId=String(form.get("profile_id")??"");
 const url=String(form.get("url")??"");
 if(!/^[0-9a-f-]{36}$/i.test(profileId))throw new Error("Select a career profile");
 const parsed=new URL(url);
 if(parsed.protocol!=="https:"||!["remotive.com","www.remotive.com","arbeitnow.com","www.arbeitnow.com"].includes(parsed.hostname))
  throw new Error("Unsupported listing source");
 const {data:profile}=await supabase.from("career_profiles").select("id").eq("id",profileId).eq("user_id",user.id).single();
 if(!profile)throw new Error("Career profile not found");
 const title=String(form.get("title")??"").slice(0,200).trim();
 if(!title)throw new Error("Missing job title");
 const {error}=await supabase.from("opportunities").upsert({
  user_id:user.id,profile_id:profileId,title,company:String(form.get("company")??"").slice(0,160),
  listing_url:parsed.toString(),location_text:String(form.get("location")??"").slice(0,160),
  work_mode:form.get("remote")==="true"?"remote":"unknown",source:String(form.get("source")??"").slice(0,60)
 },{onConflict:"user_id,listing_url"});
 if(error)throw new Error("Could not save job");
 redirect("/applications");
}
export async function queueApplication(form:FormData){
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const opportunityId=String(form.get("opportunity_id")??"");
 if(!/^[0-9a-f-]{36}$/i.test(opportunityId))throw new Error("Invalid opportunity");
 const {data:opp}=await supabase.from("opportunities").select("id").eq("id",opportunityId).eq("user_id",user.id).single();
 if(!opp)throw new Error("Opportunity not found");
 const {error}=await supabase.from("applications").upsert({user_id:user.id,opportunity_id:opportunityId,status:"pending_review"},{onConflict:"user_id,opportunity_id",ignoreDuplicates:true});
 if(error)throw new Error("Could not queue application");
 redirect("/applications");
}
