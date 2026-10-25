import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";

// Read the user's verified sent receipts on the authenticated Vercel origin,
// then send only public vacancy identifiers back to the static GitHub Pages UI.
export default async function SyncSentApplications(){
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();
 if(!user)redirect("/");
 const {data:drafts,error}=await supabase.from("recruiter_drafts")
  .select("opportunity_id,recipient_email,gmail_message_id,status")
  .eq("user_id",user.id).eq("status","sent").not("gmail_message_id","is",null)
  .order("sent_at",{ascending:false}).limit(35);
 if(error)throw new Error("Não foi possível consultar o histórico de candidaturas.");
 const ids=(drafts||[]).map(d=>d.opportunity_id);
 const {data:jobs}=ids.length?await supabase.from("opportunities").select("id,listing_url")
  .eq("user_id",user.id).in("id",ids):{data:[]};
 const lookup=new Map((jobs||[]).map(j=>[j.id,j.listing_url]));
 const records=(drafts||[]).map(d=>({url:lookup.get(d.opportunity_id)||"",email:d.recipient_email.toLowerCase()}));
 const destination=new URL("https://lucianoribeiro.github.io/ai-job-hunter/");
 destination.hash="sentReceipts="+encodeURIComponent(JSON.stringify(records));
 redirect(destination.toString());
}
