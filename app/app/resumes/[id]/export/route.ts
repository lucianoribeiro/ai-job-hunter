import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { resumeAsAtsHtml,resumeAsPlainText,ResumeData } from "@/lib/resume-export";
export async function GET(request:NextRequest,{params}:{params:Promise<{id:string}>}){
 const {id}=await params;
 if(!/^[0-9a-f-]{36}$/i.test(id)) return new NextResponse("Invalid identifier",{status:400});
 const supabase=await getSupabase();
 const {data:{user},error:authError}=await supabase.auth.getUser();
 if(authError||!user) return new NextResponse("Unauthorized",{status:401});
 const {data,error}=await supabase.from("resumes")
  .select("title,language,summary,experience,skills,education").eq("id",id).eq("user_id",user.id).single();
 if(error||!data) return new NextResponse("Not found",{status:404});
 const resume=data as ResumeData;
 const format=new URL(request.url).searchParams.get("format");
 if(format!=="txt"&&format!=="html")return new NextResponse("Invalid format",{status:400});
 const body=format==="txt"?resumeAsPlainText(resume):resumeAsAtsHtml(resume);
 return new NextResponse(body,{headers:{
  "Content-Type":format==="txt"?"text/plain; charset=utf-8":"text/html; charset=utf-8",
  "Content-Disposition":`attachment; filename="resume-${id}.${format}"`,
  "Cache-Control":"private, no-store",
  "X-Content-Type-Options":"nosniff",
  "Content-Security-Policy":"default-src 'none'; style-src 'unsafe-inline'; sandbox"
 }});
}
