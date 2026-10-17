import { NextRequest,NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { cleanPlainText } from "@/lib/resume-export";
export async function GET(request:NextRequest,{params}:{params:Promise<{id:string}>}){
 const {id}=await params;
 if(!/^[0-9a-f-]{36}$/i.test(id)) return new NextResponse("Invalid identifier",{status:400});
 const supabase=await getSupabase();
 const {data:{user},error:authError}=await supabase.auth.getUser();
 if(authError||!user) return new NextResponse("Unauthorized",{status:401});
 const {data,error}=await supabase.from("resume_versions").select("content,status")
  .eq("id",id).eq("user_id",user.id).single();
 if(error||!data)return new NextResponse("Not found",{status:404});
 if(data.status!=="approved")return new NextResponse("Resume version requires approval",{status:403});
 return new NextResponse(cleanPlainText(data.content,80000)+"\n",{headers:{
  "Content-Type":"text/plain; charset=utf-8",
  "Content-Disposition":`attachment; filename="approved-resume-${id}.txt"`,
  "Cache-Control":"private, no-store",
  "X-Content-Type-Options":"nosniff"
 }});
}
