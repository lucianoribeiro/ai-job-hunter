import Link from "next/link";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {queueApplication} from "../jobs/actions";
type Opportunity={id:string;title:string;company:string;listing_url:string;location_text:string|null;source:string};
type Application={opportunity_id:string;status:string};
type Outreach={opportunity_id:string;status:string;recipient_email:string;gmail_created_at:string|null};
export default async function Applications(){
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const [{data:rows,error},{data:appRows},{data:outreachRows}]=await Promise.all([
 supabase.from("opportunities").select("id,title,company,listing_url,location_text,source").order("created_at",{ascending:false}),
 supabase.from("applications").select("opportunity_id,status"),
 supabase.from("recruiter_drafts").select("opportunity_id,status,recipient_email,gmail_created_at").eq("user_id",user.id)
 ]);
 const opportunities=(rows??[]) as Opportunity[],apps=(appRows??[]) as Application[],outreach=(outreachRows??[]) as Outreach[];
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/jobs">← Explorar vagas</Link></header>
 <section className="panel"><span className="eyebrow">APPLICATION CENTER</span><h1>Minhas candidaturas</h1>
 <p>Salve vagas, revise o anúncio e escolha seu currículo. A plataforma não envia candidaturas sem sua ação explícita.</p>
 {error&&<p role="alert">Não foi possível carregar as vagas salvas.</p>}
 {!opportunities.length&&<p>Nenhuma vaga salva ainda. <Link href="/jobs">Explorar oportunidades →</Link></p>}
 {opportunities.map(job=>{
 const app=apps.find(a=>a.opportunity_id===job.id);
 const drafts=outreach.filter(d=>d.opportunity_id===job.id);
 const drafted=drafts.some(d=>d.status==="drafted");
 const review=drafts.some(d=>d.status==="pending_review"||d.status==="approved");
 const sent=app?.status==="applied";
 return <article className="tile" key={job.id}><h3>{job.title}</h3><p>{job.company} · {job.location_text??"Localização não informada"}</p>
 <p role="status"><strong>{sent?"Candidatura registrada como enviada":drafted?"Rascunho criado no Gmail — não enviado":review?"E-mail aguardando revisão":"CV não enviado"}</strong></p>
 {drafts.length>0&&<small>Destinatário: {drafts[0].recipient_email}</small>}
 {app&&<small> · Status do processo: {app.status}</small>}
 <div className="controls"><Link href={`/applications/outreach?job=${encodeURIComponent(job.id)}`}>Preparar e-mail ao recrutador →</Link><a href={job.listing_url} rel="noopener noreferrer" target="_blank">Candidatar-me no site da empresa ↗</a>
 {!app&&<form action={queueApplication}><input type="hidden" name="opportunity_id" value={job.id}/><button>Preparar candidatura</button></form>}</div>
 <p className="note">Antes de enviar: confirme requisitos, localização, recrutador e versão do CV no <Link href="/resumes">Resume Studio</Link>.</p></article>})}</section></main>;
}
