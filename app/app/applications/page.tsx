import Link from "next/link";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {queueApplication} from "../jobs/actions";
type Opportunity={id:string;title:string;company:string;listing_url:string;location_text:string|null;source:string};
type Application={opportunity_id:string;status:string};
export default async function Applications(){
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const [{data:rows,error},{data:appRows}]=await Promise.all([
 supabase.from("opportunities").select("id,title,company,listing_url,location_text,source").order("created_at",{ascending:false}),
 supabase.from("applications").select("opportunity_id,status")
 ]);
 const opportunities=(rows??[]) as Opportunity[],apps=(appRows??[]) as Application[];
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/jobs">← Explorar vagas</Link></header>
 <section className="panel"><span className="eyebrow">APPLICATION CENTER</span><h1>Minhas candidaturas</h1>
 <p>Salve vagas, revise o anúncio e escolha seu currículo. A plataforma não envia candidaturas sem sua ação explícita.</p>
 {error&&<p role="alert">Não foi possível carregar as vagas salvas.</p>}
 {!opportunities.length&&<p>Nenhuma vaga salva ainda. <Link href="/jobs">Explorar oportunidades →</Link></p>}
 {opportunities.map(job=>{
 const app=apps.find(a=>a.opportunity_id===job.id);
 return <article className="tile" key={job.id}><h3>{job.title}</h3><p>{job.company} · {job.location_text??"Localização não informada"}</p>
 <small>{app?"Status: "+app.status:"Ainda não iniciada"}</small>
 <div className="controls"><a href={job.listing_url} rel="noopener noreferrer" target="_blank">Candidatar-me no site da empresa ↗</a>
 {!app&&<form action={queueApplication}><input type="hidden" name="opportunity_id" value={job.id}/><button>Preparar candidatura</button></form>}</div>
 <p className="note">Antes de enviar: confirme requisitos, localização, recrutador e versão do CV no <Link href="/resumes">Resume Studio</Link>.</p></article>})}</section></main>;
}
