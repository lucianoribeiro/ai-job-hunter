import Link from "next/link";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {createOutreachDraft,approveOutreachDraft} from "./actions";
type Job={id:string;title:string;company:string;listing_url:string};
type Version={id:string;label:string;target_role:string};
type Draft={id:string;recipient_email:string;subject:string;body:string;status:string;resume_version_id:string|null};
export default async function Outreach({searchParams}:{searchParams:Promise<{job?:string}>}){
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const [{data:jobsRows},{data:versionsRows},{data:draftsRows}]=await Promise.all([
 supabase.from("opportunities").select("id,title,company,listing_url").order("created_at",{ascending:false}),
 supabase.from("resume_versions").select("id,label,target_role").eq("status","approved").order("created_at",{ascending:false}),
 supabase.from("recruiter_drafts").select("id,recipient_email,subject,body,status,resume_version_id").order("created_at",{ascending:false})
 ]);
 const jobs=(jobsRows??[]) as Job[],versions=(versionsRows??[]) as Version[],drafts=(draftsRows??[]) as Draft[];
 const jobId=(await searchParams).job;const selected=jobs.find(j=>j.id===jobId)??jobs[0];
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/applications">← Minhas candidaturas</Link></header>
 <section className="panel"><span className="eyebrow">RECRUITER OUTREACH</span><h1>Preparar mensagem ao recrutador</h1>
 <p>Use somente um endereço profissional divulgado explicitamente para receber candidaturas. Confira a vaga e revise a mensagem antes de aprovar.</p>
 {!jobs.length?<p>Salve uma vaga antes de preparar o contato. <Link href="/jobs">Ver vagas →</Link></p>:
 <form action={createOutreachDraft} className="form">
 <label>Oportunidade<select name="opportunity_id" defaultValue={selected?.id} required>{jobs.map(j=><option key={j.id} value={j.id}>{j.title} — {j.company}</option>)}</select></label>
 <label>E-mail divulgado pelo recrutador<input name="recipient" type="email" required maxLength={254} placeholder="recrutamento@empresa.com"/></label>
 <label>Assunto<input name="subject" required maxLength={250} defaultValue={selected?`Application — ${selected.title}`:"Application"}/></label>
 <label>Mensagem<textarea name="body" required rows={10} maxLength={12000} placeholder="Hello, I am interested in the position..."/></label>
 <label>Versão do currículo (opcional nesta etapa)<select name="resume_version_id"><option value="">Selecionar depois</option>{versions.map(v=><option key={v.id} value={v.id}>{v.label} — {v.target_role}</option>)}</select></label>
 <p className="note">A versão do currículo é apenas referenciada. Nenhum arquivo é anexado ou enviado por e-mail nesta etapa.</p>
 <button className="primary">Salvar para revisão</button></form>}
 </section><section className="panel"><h2>Mensagens preparadas</h2>
 {!drafts.length&&<p>Nenhuma mensagem preparada.</p>}
 {drafts.map(d=><article className="tile" key={d.id}><h3>{d.subject}</h3><p>Para: {d.recipient_email}</p>
 <small>{d.status==="approved"?"Aprovado para uso futuro":"Aguardando revisão"}</small>
 <details><summary>Revisar mensagem</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{d.body}</pre></details>
 {d.status==="approved"&&<p><Link href={`/applications/outreach/${d.id}/compose`}>Abrir mensagem aprovada no Gmail →</Link></p>}
 {d.status==="pending_review"&&<form action={approveOutreachDraft}><input type="hidden" name="draft_id" value={d.id}/><button>Confirmar conteúdo</button></form>}
 </article>)}</section>
 <p className="note">Aprovar aqui não envia e-mail nem cria rascunho no Gmail. Integração Gmail autenticada e anexo real do CV ainda são pendentes.</p></main>;
}
