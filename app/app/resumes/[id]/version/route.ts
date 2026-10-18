import { NextRequest,NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { cleanPlainText } from "@/lib/resume-export";
import {professionalResumePdf,safeResumeFilename} from "@/lib/resume-pdf";
export async function GET(request:NextRequest,{params}:{params:Promise<{id:string}>}){
 const {id}=await params;
 if(!/^[0-9a-f-]{36}$/i.test(id)) return new NextResponse("Invalid identifier",{status:400});
 const supabase=await getSupabase();
 const {data:{user},error:authError}=await supabase.auth.getUser();
 if(authError||!user) return new NextResponse("Unauthorized",{status:401});
 const {data,error}=await supabase.from("resume_versions").select("content,status,target_role,label")
  .eq("id",id).eq("user_id",user.id).single();
 if(error||!data)return new NextResponse("Not found",{status:404});
 if(data.status!=="approved")return new NextResponse("Resume version requires approval",{status:403});
 const pdf=await professionalResumePdf(cleanPlainText(data.content,80000),data.target_role||data.label||"Professional Resume");
 return new NextResponse(Buffer.from(pdf),{headers:{
  "Content-Type":"application/pdf",
  "Content-Disposition":`attachment; filename="${safeResumeFilename(data.target_role||data.label||"Professional_CV")}"`,
  "Cache-Control":"private, no-store",
  "X-Content-Type-Options":"nosniff"
 }});
}
