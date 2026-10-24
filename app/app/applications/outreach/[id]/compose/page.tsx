import Link from "next/link";
import {redirect,notFound} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {connectGmail} from "@/app/actions";
import {createApprovedGmailDraft,sendApprovedRecruiterEmail} from "./actions";
type Draft={id:string;recipient_email:string;subject:string;body:string;status:string;resume_version_id:string|null;resume_file_id:string|null;opportunity_id:string};
export default async function Compose({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{gmail?:string}>}){
 const {id}=await params;
 if(!/^[a-f0-9-]{36}$/i.test(id))notFound();
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();
 if(!user)redirect("/");
 const {data,error}=await supabase.from("recruiter_drafts").select("id,recipient_email,subject,body,status,resume_version_id,resume_file_id,opportunity_id,gmail_message_id,sent_at")
  .eq("id",id).eq("user_id",user.id).single();
 if(error||!data)notFound();
 const draft=data as Draft;
 if(!["approved","drafted","sending","sent"].includes(draft.status))return <main className="shell"><section className="panel"><h1>Revisão necessária</h1><p>Confirme a mensagem antes de criar o rascunho no Gmail.</p><Link href="/applications/outreach">Voltar aos rascunhos</Link></section></main>;
 let versionStatus:string|undefined;
 if(draft.resume_version_id){
  const {data:v}=await supabase.from("resume_versions").select("status").eq("id",draft.resume_version_id).eq("user_id",user.id).single();
  versionStatus=v?.status;
 }
 const canDownload=!!draft.resume_file_id || (!!draft.resume_version_id&&versionStatus==="approved");
 const gmail=(await searchParams).gmail;
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/applications/outreach">← Revisar candidaturas</Link></header>
 <section className="panel"><span className="eyebrow">RASCUNHO GMAIL COM CV</span><h1>Revisar e criar rascunho</h1>
 <p>Confira destinatário, texto e CV. Você pode criar um rascunho ou autorizar explicitamente o envio da candidatura. Nenhum e-mail é enviado ao carregar a página.</p>
 <div className="tile"><p><strong>Destinatário:</strong> {draft.recipient_email}</p><p><strong>Assunto:</strong> {draft.subject}</p>
 <details open><summary>Mensagem aprovada</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{draft.body}</pre></details></div>
 {gmail==="connect"&&<form action={connectGmail}><input type="hidden" name="next" value={`/applications/outreach/${draft.id}/compose`}/><p role="status">Autorize o acesso restrito para criar rascunhos no Gmail.</p><button className="primary">Conectar Gmail com OAuth</button></form>}
 {draft.status==="sent"?<p role="status">✅ CV enviado pelo Gmail e registrado. Não reenvie para o mesmo recrutador.</p>:draft.status==="sending"?<p role="alert">Envio em verificação. Confira o Gmail antes de tentar outra candidatura.</p>:gmail==="created"||draft.status==="drafted"?<p role="status">Rascunho criado com o CV em PDF anexado. Revise-o no Gmail antes de enviar.</p>:canDownload&&<form action={createApprovedGmailDraft}><input type="hidden" name="draft_id" value={draft.id}/><button className="primary">Criar rascunho no Gmail com CV</button></form>}
 {draft.status==="approved"&&canDownload&&<form action={sendApprovedRecruiterEmail}><input type="hidden" name="draft_id" value={draft.id}/><button className="primary">Confirmar e enviar e-mail com CV</button><p className="note">Esta ação envia realmente o e-mail ao destinatário informado.</p></form>}
 <div className="controls">{(gmail==="created"||draft.status==="drafted")&&<a className="primary" href="https://mail.google.com/mail/u/0/#drafts" target="_blank" rel="noopener noreferrer">Abrir rascunhos no Gmail ↗</a>}
 {draft.resume_file_id&&<p>O PDF privado selecionado será anexado ao rascunho.</p>}
 {draft.resume_version_id&&versionStatus==="approved"&&!draft.resume_file_id&&<a href={`/resumes/${draft.resume_version_id}/version`}>Baixar CV profissional (PDF) ↓</a>}</div>
 {!canDownload&&<p role="status">Ainda não há currículo aprovado associado. Selecione um CV no Resume Studio antes de enviar a candidatura.</p>}
 <p className="note">A autorização Gmail solicita permissões de rascunho e envio. O envio acontece somente após clicar em Confirmar e enviar. Tokens OAuth não são armazenados no banco.</p>
 </section></main>;
}
