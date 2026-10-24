import {recruiterMessage} from "@/lib/recruiter-template";
import Link from "next/link";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {createOutreachDraft,approveOutreachDraft} from "./actions";
type Job={id:string;title:string;company:string;listing_url:string};
type Version={id:string;label:string;target_role:string};
type Pdf={id:string;label:string;language:string};
type Draft={id:string;recipient_email:string;subject:string;body:string;status:string;resume_version_id:string|null;resume_file_id:string|null};
export default async function Outreach({searchParams}:{searchParams:Promise<{job?:string;recipient?:string;title?:string;source?:string}>}){
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const [{data:jobsRows},{data:versionsRows},{data:draftsRows},{data:pdfRows}]=await Promise.all([
 supabase.from("opportunities").select("id,title,company,listing_url").order("created_at",{ascending:false}),
 supabase.from("resume_versions").select("id,label,target_role").eq("status","approved").order("created_at",{ascending:false}),
 supabase.from("recruiter_drafts").select("id,recipient_email,subject,body,status,resume_version_id,resume_file_id").order("created_at",{ascending:false}),
 supabase.from("resume_files").select("id,label,language").eq("user_id",user.id)
 ]);
 const jobs=(jobsRows??[]) as Job[],versions=(versionsRows??[]) as Version[],drafts=(draftsRows??[]) as Draft[],pdfs=(pdfRows??[]) as Pdf[];
 const params=await searchParams,external=/^https:\/\//i.test(params.source||"")&&!!params.title;
 const selected=jobs.find(j=>j.id===params.job||j.listing_url===params.source)??jobs[0];
 const displayTitle=(params.title||selected?.title||"oportunidade").slice(0,160),displayCompany=selected?.company||"empresa";
 const person=String(user.user_metadata?.full_name||user.user_metadata?.name||"").trim();
 const template=recruiterMessage({title:displayTitle,company:displayCompany==="empresa"?"":displayCompany,name:person,language:/\b(QA|SDET|Engineer|Manager|Lead|Project|Analyst)\b/i.test(displayTitle)?"en":"pt"});
 const defaultSubject=template.subject;
 const defaultBody=template.body;
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/applications">← Minhas candidaturas</Link></header>
 <section className="panel"><span className="eyebrow">RECRUITER OUTREACH</span><h1>Preparar mensagem ao recrutador</h1>
 <p>Use somente um endereço profissional divulgado explicitamente para receber candidaturas. Confira a vaga e revise a mensagem antes de aprovar.</p>
 {!jobs.length?<p>Salve uma vaga antes de preparar o contato. <Link href="/jobs">Ver vagas →</Link></p>:
 <form action={createOutreachDraft} className="form">
 <label>Oportunidade<select name="opportunity_id" defaultValue={external&&!jobs.some(j=>j.listing_url===params.source)?"import":selected?.id} required>{external&&!jobs.some(j=>j.listing_url===params.source)&&<option value="import">{displayTitle} — Recruiter Monitor</option>}{jobs.map(j=><option key={j.id} value={j.id}>{j.title} — {j.company}</option>)}</select></label>
 <input type="hidden" name="listing_url" value={params.source||""}/><input type="hidden" name="listing_title" value={displayTitle}/>
 <label>E-mail divulgado pelo recrutador<input name="recipient" type="email" required maxLength={254} defaultValue={params.recipient||""} placeholder="recrutamento@empresa.com"/></label>
 <label>Assunto<input name="subject" required maxLength={250} defaultValue={defaultSubject}/></label>
 <label>Mensagem<textarea name="body" required rows={10} maxLength={12000} defaultValue={defaultBody}/></label>
 <label>PDF privado para anexar<select name="resume_file_id"><option value="">Usar currículo gerado pelo Resume Studio</option>{pdfs.map(p=><option key={p.id} value={p.id}>{p.label} ({p.language})</option>)}</select></label>
 <label>Alternativa: versão aprovada do Resume Studio<select name="resume_version_id"><option value="">Selecione o currículo</option>{versions.map(v=><option key={v.id} value={v.id}>{v.label} — {v.target_role}</option>)}</select></label>
 <p className="note">Se escolher um PDF privado, ele terá prioridade sobre a versão gerada. A aprovação apenas prepara um rascunho no Gmail; não envia a candidatura.</p>
 <button className="primary">Salvar para revisão</button></form>}
 </section><section className="panel"><h2>Mensagens preparadas</h2>
 {!drafts.length&&<p>Nenhuma mensagem preparada.</p>}
 {drafts.map(d=><article className="tile" key={d.id}><h3>{d.subject}</h3><p>Para: {d.recipient_email}</p>
 <small>{d.status==="drafted"?"Rascunho criado no Gmail":d.status==="approved"?"Aprovado para criar no Gmail":"Aguardando revisão"}</small>
 <details><summary>Revisar mensagem</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{d.body}</pre></details>
 {["approved","drafted"].includes(d.status)&&<p><Link href={`/applications/outreach/${d.id}/compose`}>Revisar integração Gmail →</Link></p>}
 {d.status==="pending_review"&&<form action={approveOutreachDraft}><input type="hidden" name="draft_id" value={d.id}/><button>Confirmar conteúdo</button></form>}
 </article>)}</section>
 <p className="note">Aprovar não envia e-mail. Na etapa seguinte, você autoriza a criação de um rascunho Gmail com o CV em PDF anexado.</p></main>;
}
