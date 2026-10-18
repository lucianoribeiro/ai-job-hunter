import Link from "next/link";
import {redirect,notFound} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {connectGmail} from "@/app/actions";
import {createApprovedGmailDraft} from "./actions";
type Draft={id:string;recipient_email:string;subject:string;body:string;status:string;resume_version_id:string|null;opportunity_id:string};
export default async function Compose({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{gmail?:string}>}){
 const {id}=await params;
 if(!/^[a-f0-9-]{36}$/i.test(id))notFound();
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();
 if(!user)redirect("/");
 const {data,error}=await supabase.from("recruiter_drafts").select("id,recipient_email,subject,body,status,resume_version_id,opportunity_id")
  .eq("id",id).eq("user_id",user.id).single();
 if(error||!data)notFound();
 const draft=data as Draft;
 if(!["approved","drafted"].includes(draft.status))return <main className="shell"><section className="panel"><h1>Revisão necessária</h1><p>Confirme a mensagem antes de criar o rascunho no Gmail.</p><Link href="/applications/outreach">Voltar aos rascunhos</Link></section></main>;
 let versionStatus:string|undefined;
 if(draft.resume_version_id){
  const {data:v}=await supabase.from("resume_versions").select("status").eq("id",draft.resume_version_id).eq("user_id",user.id).single();
  versionStatus=v?.status;
 }
 const canDownload=!!draft.resume_version_id&&versionStatus==="approved";
 const gmail=(await searchParams).gmail;
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/applications/outreach">← Revisar candidaturas</Link></header>
 <section className="panel"><span className="eyebrow">RASCUNHO GMAIL COM CV</span><h1>Revisar e criar rascunho</h1>
 <p>Confira destinatário, mensagem e currículo. A ação cria um rascunho com PDF anexado; nunca envia o e-mail.</p>
 <div className="tile"><p><strong>Destinatário:</strong> {draft.recipient_email}</p><p><strong>Assunto:</strong> {draft.subject}</p>
 <details open><summary>Mensagem aprovada</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{draft.body}</pre></details></div>
 {gmail==="connect"&&<form action={connectGmail}><input type="hidden" name="next" value={`/applications/outreach/${draft.id}/compose`}/><p role="status">Autorize o acesso restrito para criar rascunhos no Gmail.</p><button className="primary">Conectar Gmail com OAuth</button></form>}
 {gmail==="created"||draft.status==="drafted"?<p role="status">Rascunho criado com o CV em PDF anexado. Revise-o no Gmail antes de enviar.</p>:canDownload&&<form action={createApprovedGmailDraft}><input type="hidden" name="draft_id" value={draft.id}/><button className="primary">Criar rascunho no Gmail com CV</button></form>}
 <div className="controls">{(gmail==="created"||draft.status==="drafted")&&<a className="primary" href="https://mail.google.com/mail/u/0/#drafts" target="_blank" rel="noopener noreferrer">Abrir rascunhos no Gmail ↗</a>}
 {canDownload&&<a href={`/resumes/${draft.resume_version_id}/version`}>Baixar CV profissional (PDF) ↓</a>}</div>
 {!canDownload&&<p role="status">Ainda não há currículo aprovado associado. Selecione um CV no Resume Studio antes de enviar a candidatura.</p>}
 <p className="note">O acesso solicitado permite apenas criar e gerenciar rascunhos. O envio continua sendo uma ação manual no Gmail. Tokens OAuth não são armazenados no banco.</p>
 </section></main>;
}
