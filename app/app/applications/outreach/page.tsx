import {recruiterMessage,vacancyTitle,vacancyLanguage} from "@/lib/recruiter-template";
import Link from "next/link";
import {redirect} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {createOutreachDraft,approveOutreachDraft} from "./actions";
import {connectGmail} from "@/app/actions";
import {gmailAuthorization} from "@/lib/gmail-auth";
type Job={id:string;title:string;company:string;listing_url:string};
type Version={id:string;label:string;target_role:string};
type Pdf={id:string;label:string;language:string;created_at:string};
type Draft={id:string;recipient_email:string;subject:string;body:string;status:string;resume_version_id:string|null;resume_file_id:string|null;gmail_message_id:string|null;sent_at:string|null;opportunity_id:string};
export default async function Outreach({searchParams}:{searchParams:Promise<{job?:string;recipient?:string;title?:string;source?:string;description?:string;view?:string;sent?:string}>}){
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();if(!user)redirect("/");
 const [{data:jobsRows},{data:versionsRows},{data:draftsRows},{data:pdfRows}]=await Promise.all([
 supabase.from("opportunities").select("id,title,company,listing_url").order("created_at",{ascending:false}),
 supabase.from("resume_versions").select("id,label,target_role").eq("status","approved").order("created_at",{ascending:false}),
 supabase.from("recruiter_drafts").select("id,opportunity_id,recipient_email,subject,body,status,resume_version_id,resume_file_id,gmail_message_id,sent_at").order("created_at",{ascending:false}),
 supabase.from("resume_files").select("id,label,language,created_at").eq("user_id",user.id).order("created_at",{ascending:false})
 ]);
 const jobs=(jobsRows??[]) as Job[],versions=(versionsRows??[]) as Version[],drafts=(draftsRows??[]) as Draft[],pdfs=(pdfRows??[]) as Pdf[];
 const params=await searchParams,external=/^https:\/\//i.test(params.source||"")&&!!params.title;
 const selected=jobs.find(j=>j.id===params.job||j.listing_url===params.source)??(external?undefined:jobs[0]);
 const displayTitle=vacancyTitle(params.title||selected?.title||"oportunidade"),displayCompany=selected?.company||"empresa";
 const detectedLanguage=vacancyLanguage(params.title||displayTitle,params.description||"");
 const person=String(user.user_metadata?.full_name||user.user_metadata?.name||"").trim();
 const template=recruiterMessage({title:displayTitle,company:displayCompany==="empresa"?"":displayCompany,name:person,description:params.description||"",language:detectedLanguage});
 const preferredLanguage=detectedLanguage==="en"?"en-US":"pt-BR";
 const preferredPdf=pdfs.find(p=>p.language===preferredLanguage)||pdfs[0];
 const defaultSubject=template.subject;
 const defaultBody=template.body;
 const {data:sessionInfo}=await supabase.auth.getSession();
 const gmail=await gmailAuthorization(sessionInfo.session?.provider_token);
 const sentDrafts=drafts.filter(d=>d.status==="sent"&&!!d.gmail_message_id);
 const visibleDrafts=params.view==="sent"?sentDrafts:drafts;
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/applications">← Minhas candidaturas</Link></header>
 <section className="panel"><span className="eyebrow">RECRUITER OUTREACH</span><h1>Preparar mensagem ao recrutador</h1>
 <p>Revise destinatário, cargo, mensagem e CV nesta tela. Ao clicar em <strong>Enviar candidatura</strong>, o Gmail enviará a mensagem com o PDF anexado. Não será necessária uma segunda aprovação.</p>
 <p><Link href="/applications/outreach?view=sent">✅ Candidaturas enviadas ({sentDrafts.length}) →</Link></p>
 {!gmail.canSend&&<form action={connectGmail}><input type="hidden" name="next" value="/applications/outreach"/><p role="alert">Para enviar, conecte sua conta Google e autorize a permissão Gmail.</p><button className="primary" type="submit">Conectar Gmail para enviar</button></form>}
 {!jobs.length&&!external?<p>Salve uma vaga antes de preparar o contato. <Link href="/jobs">Ver vagas →</Link></p>:
 <form action={createOutreachDraft} className="form">
 <label>Oportunidade<select name="opportunity_id" defaultValue={external&&!jobs.some(j=>j.listing_url===params.source)?"import":selected?.id} required>{external&&!jobs.some(j=>j.listing_url===params.source)&&<option value="import">{displayTitle} — Recruiter Monitor</option>}{jobs.map(j=><option key={j.id} value={j.id}>{j.title} — {j.company}</option>)}</select></label>
 <input type="hidden" name="listing_url" value={params.source||""}/><input type="hidden" name="listing_title" value={displayTitle}/>
 {!params.recipient&&<p role="status">O índice público não informou um endereço de e-mail para esta vaga. Confirme no anúncio original e informe o destinatário profissional antes de continuar.</p>}
 <label>E-mail divulgado pelo recrutador<input name="recipient" type="email" required maxLength={254} defaultValue={params.recipient||""} placeholder="recrutamento@empresa.com"/></label>
 <p role="status">Idioma identificado para o e-mail: <strong>{detectedLanguage==="en"?"Inglês":"Português"}</strong>. Revise antes de enviar.</p>
 <label>Assunto<input name="subject" required maxLength={250} defaultValue={defaultSubject}/></label>
 <label>Mensagem<textarea name="body" required rows={10} maxLength={12000} defaultValue={defaultBody}/></label>
 <label>PDF privado para anexar<select name="resume_file_id" defaultValue={preferredPdf?.id||""}><option value="">Usar currículo gerado pelo Resume Studio</option>{pdfs.map(p=><option key={p.id} value={p.id}>{p.label} ({p.language})</option>)}</select></label>
 <label>Alternativa: versão aprovada do Resume Studio<select name="resume_version_id"><option value="">Selecione o currículo</option>{versions.map(v=><option key={v.id} value={v.id}>{v.label} — {v.target_role}</option>)}</select></label>
 {preferredPdf&&<p role="status">✅ CV selecionado para anexar: <strong>{preferredPdf.label}</strong> ({preferredPdf.language==="en-US"?"Inglês":"Português"}). Confirme o documento antes de enviar.</p>}
 {!pdfs.length&&<p role="alert">Nenhum CV em PDF salvo. <Link href="/resumes">Enviar currículo primeiro</Link>.</p>}
 <p className="note">Se escolher um PDF privado, ele terá prioridade sobre a versão gerada. A aprovação apenas prepara um rascunho no Gmail; não envia a candidatura.</p>
 <button className="primary" type="submit" disabled={!gmail.canSend||!preferredPdf&&!versions.length}>✉ Enviar candidatura com CV</button><p className="note">Ao clicar, o e-mail será enviado imediatamente pelo Gmail ao destinatário informado. Não existe etapa adicional de revisão.</p></form>}
 </section><section className="panel"><h2>{params.view==="sent"?"Candidaturas enviadas":"Histórico de candidaturas"}</h2><p><Link href="/applications/outreach?view=sent">Ver somente enviadas ({sentDrafts.length})</Link> · <Link href="/applications/outreach">Ver todas</Link></p>
 {params.sent&&<p role="status">✅ Gmail confirmou o envio e a candidatura foi registrada.</p>}
 {!visibleDrafts.length&&<p>Nenhuma candidatura nesta visualização.</p>}
 {visibleDrafts.map(d=><article className="tile" key={d.id}><h3>{d.subject}</h3><p>Para: {d.recipient_email}</p>
 {d.sent_at&&<p><strong>Enviada em:</strong> {new Date(d.sent_at).toLocaleString("pt-BR",{timeZone:"America/Sao_Paulo"})}</p>}
 <small>{d.status==="sent"&&d.gmail_message_id?"✅ CV enviado pelo Gmail":d.status==="sending"?"Envio em verificação — confira o Gmail":d.status==="drafted"?"Rascunho criado no Gmail":d.status==="approved"?"Aprovado para criar no Gmail":"Aguardando revisão"}</small>
 {d.status==="sent"&&jobs.find(j=>j.id===d.opportunity_id)?.listing_url&&<p><a href={"https://lucianoribeiro.github.io/ai-job-hunter/#sent="+encodeURIComponent(jobs.find(j=>j.id===d.opportunity_id)!.listing_url)} >Voltar à vaga e marcar envio neste navegador ↗</a></p>}
 <details><summary>Revisar mensagem</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{d.body}</pre></details>
 {["approved","drafted","sent","sending"].includes(d.status)&&<p><Link href={`/applications/outreach/${d.id}/compose`}>Revisar integração Gmail →</Link></p>}
 {d.status==="pending_review"&&<form action={approveOutreachDraft}><input type="hidden" name="draft_id" value={d.id}/><button>Confirmar conteúdo</button></form>}
 </article>)}</section>
 <p className="note">O histórico de envios confirmados permanece no Supabase. A marcação no GitHub Pages é local ao navegador e pode não aparecer em outro dispositivo.</p></main>;
}
