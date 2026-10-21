import Link from "next/link";
import { redirect } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import { fetchRecentJobs,matchingJobs } from "@/lib/job-feed";
import { saveJob } from "./actions";
import { recruiterEmails } from "@/lib/recruiter-email";
type Profile={id:string;label:string;target_roles:string[]};
export default async function Jobs({searchParams}:{searchParams:Promise<{profile?:string;mode?:string}>}){
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const {data}=await supabase.from("career_profiles").select("id,label,target_roles").order("created_at",{ascending:false});
 const profiles=(data??[]) as Profile[];const params=await searchParams;
 const selected=profiles.find(p=>p.id===params.profile)??profiles[0];
 const remote=params.mode!=="all";
 const [{data:savedJobs},{data:applications},{data:drafts}]=await Promise.all([
  supabase.from("opportunities").select("id,listing_url").eq("user_id",user.id),
  supabase.from("applications").select("opportunity_id,status").eq("user_id",user.id),
  supabase.from("recruiter_drafts").select("opportunity_id,status").eq("user_id",user.id)
 ]);
 const savedByUrl=new Map((savedJobs??[]).map(j=>[String(j.listing_url).split("?")[0].replace(/[/]$/,""),j.id]));
 const appById=new Map((applications??[]).map(a=>[a.opportunity_id,a.status]));
 const draftsById=new Map<string,string[]>();
 for(const d of drafts??[])draftsById.set(d.opportunity_id,[...(draftsById.get(d.opportunity_id)||[]),d.status]);
 const feed=await fetchRecentJobs();
 const filtered=matchingJobs(feed.jobs,selected?.target_roles??[],remote).slice(0,40);
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><nav><Link href="/dashboard">Meu perfil</Link> · <Link href="/applications">Candidaturas</Link></nav></header>
 <section className="panel"><span className="eyebrow">OPORTUNIDADES RECENTES</span><h1>Encontre sua próxima vaga</h1>
 <p>Vagas de fontes públicas, ordenadas pela data informada pela origem. Atualizações são armazenadas em cache por até 15 minutos.</p>
 <form action="/jobs" method="get" className="form">
 <label>Perfil profissional<select name="profile" defaultValue={selected?.id}>{profiles.map(p=><option value={p.id} key={p.id}>{p.label}</option>)}</select></label>
 <label>Modalidade<select name="mode" defaultValue={remote?"remote":"all"}><option value="remote">Remoto primeiro</option><option value="all">Todas as modalidades</option></select></label>
 <button className="primary">Atualizar filtros</button></form>
 {!selected&&<p role="status">Cadastre seu perfil no <Link href="/dashboard">dashboard</Link> para filtrar e salvar vagas.</p>}
 {feed.warnings.map(w=><p className="note" key={w}>{w}</p>)}
 <p role="status">{filtered.length} oportunidades encontradas para os filtros selecionados. A elegibilidade para candidatos no Brasil deve ser confirmada em cada anúncio.</p>
 <div className="jobs">{filtered.map(job=>{const matched=savedByUrl.get(job.url.split("?")[0].replace(/[/]$/,""));const statuses=matched?(draftsById.get(matched)||[]):[];const appStatus=matched?appById.get(matched):undefined;const emails=recruiterEmails(job.description);const label=statuses.includes("drafted")?"Rascunho Gmail criado — não enviado":statuses.some(s=>s==="approved"||s==="pending_review")?"Candidatura em preparação":appStatus==="applied"?"Candidatura declarada como enviada (não verificada)":matched?"Vaga salva — CV não enviado":"CV não enviado";return <article className="tile" key={job.id}>
 <div className="row"><h3>{job.title}</h3><span className="pill">{job.remote?"Remoto":"Localização a verificar"}</span></div><p role="status"><strong>{label}</strong></p>
 <p>{job.company} · {job.location||"Localização não informada"}</p>
 <small>{job.source} · {job.published?new Date(job.published).toLocaleDateString("pt-BR",{timeZone:"UTC"}):"Publicação sem data"}</small>
 <p>{job.description.slice(0,230)}{job.description.length>230?"…":""}</p>
 {emails.length>0&&<p><strong>E-mail publicado no anúncio (verificar):</strong> {emails.join(", ")}</p>}
 {matched&&emails.length>0&&<p><Link href={`/applications/outreach?job=${encodeURIComponent(matched)}&recipient=${encodeURIComponent(emails[0])}`}>Preparar contato com e-mail identificado →</Link></p>}
 <div className="controls"><a href={job.url} target="_blank" rel="noopener noreferrer">Ver vaga original ↗</a>
 {selected&&<form action={saveJob}><input type="hidden" name="profile_id" value={selected.id}/>
 <input type="hidden" name="url" value={job.url}/><input type="hidden" name="title" value={job.title}/><input type="hidden" name="company" value={job.company}/>
 <input type="hidden" name="location" value={job.location}/><input type="hidden" name="remote" value={String(job.remote)}/><input type="hidden" name="source" value={job.source}/>
 <button type="submit">Salvar oportunidade</button></form>}</div></article>})}</div></section>
 </main>;
}
