import Link from "next/link";
import {redirect,notFound} from "next/navigation";
import {getSupabase} from "@/lib/supabase";
import {gmailComposeUrl} from "@/lib/gmail-compose";
type Draft={id:string;recipient_email:string;subject:string;body:string;status:string;resume_version_id:string|null;opportunity_id:string};
export default async function Compose({params}:{params:Promise<{id:string}>}){
 const {id}=await params;
 if(!/^[a-f0-9-]{36}$/i.test(id))notFound();
 const supabase=await getSupabase();const {data:{user}}=await supabase.auth.getUser();
 if(!user)redirect("/");
 const {data,error}=await supabase.from("recruiter_drafts").select("id,recipient_email,subject,body,status,resume_version_id,opportunity_id")
  .eq("id",id).eq("user_id",user.id).single();
 if(error||!data)notFound();
 const draft=data as Draft;
 if(draft.status!=="approved")return <main className="shell"><section className="panel"><h1>Revisão necessária</h1><p>Confirme a mensagem antes de abrir o Gmail.</p><Link href="/applications/outreach">Voltar aos rascunhos</Link></section></main>;
 let versionStatus:string|undefined;
 if(draft.resume_version_id){
  const {data:v}=await supabase.from("resume_versions").select("status").eq("id",draft.resume_version_id).eq("user_id",user.id).single();
  versionStatus=v?.status;
 }
 const canDownload=!!draft.resume_version_id&&versionStatus==="approved";
 const composeUrl=gmailComposeUrl(draft.recipient_email,draft.subject,draft.body);
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/applications/outreach">← Revisar candidaturas</Link></header>
 <section className="panel"><span className="eyebrow">PRONTO PARA COMPOR</span><h1>Revisar e abrir Gmail</h1>
 <p>Confira o endereço e o anúncio original antes de prosseguir. Abrir o Gmail não envia nenhuma mensagem.</p>
 <div className="tile"><p><strong>Destinatário:</strong> {draft.recipient_email}</p><p><strong>Assunto:</strong> {draft.subject}</p>
 <details open><summary>Mensagem aprovada</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{draft.body}</pre></details></div>
 <div className="controls"><a className="primary" href={composeUrl} target="_blank" rel="noopener noreferrer">Abrir composição no Gmail ↗</a>
 {canDownload&&<a href={`/resumes/${draft.resume_version_id}/version`}>Baixar CV aprovado (TXT) ↓</a>}</div>
 {!canDownload&&<p role="status">Ainda não há currículo aprovado associado. Selecione um CV no Resume Studio antes de enviar a candidatura.</p>}
 <p className="note">Anexe manualmente o currículo no Gmail, verifique o remetente e clique em Enviar somente quando desejar. O sistema não tem acesso à sua caixa postal e não registra o envio automaticamente.</p>
 </section></main>;
}
