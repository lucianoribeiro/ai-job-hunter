import { getSupabase } from "@/lib/supabase";
import { NextResponse } from "next/server";
export async function GET(request: Request) {
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();
 if(!user) return new NextResponse("Unauthorized",{status:401});
 const id=new URL(request.url).searchParams.get("id") || "";
 if(!/^[0-9a-f-]{36}$/i.test(id)) return new NextResponse("Invalid identifier",{status:400});
 const {data,error}=await supabase.from("resume_files").select("object_path").eq("id",id).eq("user_id",user.id).single();
 if(error||!data) return new NextResponse("Not found",{status:404});
 const {data:pdf,error:downloadError}=await supabase.storage.from("private-resumes").download(data.object_path);
 if(downloadError||!pdf) return new NextResponse("Unavailable",{status:404});
 return new NextResponse(pdf.stream(),{headers:{"Content-Type":"application/pdf","Content-Disposition":"attachment; filename=resume.pdf","Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}});
}
