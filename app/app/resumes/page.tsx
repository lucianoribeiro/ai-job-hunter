import Link from "next/link";
import { redirect } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import { approveVersion, createResume, createVersion } from "./actions";
type Resume={id:string;title:string;language:string;summary:string;experience:string;skills:string;education:string};
type Version={id:string;resume_id:string;label:string;target_role:string;content:string;status:string};
export default async function ResumeStudio(){
 const supabase=await getSupabase();
 const {data:{user},error}=await supabase.auth.getUser();
 if(error||!user) redirect("/");
 const [{data:resumeRows,error:resumeError},{data:versionRows,error:versionError}]=await Promise.all([
  supabase.from("resumes").select("id,title,language,summary,experience,skills,education").order("created_at",{ascending:false}),
  supabase.from("resume_versions").select("id,resume_id,label,target_role,content,status").order("created_at",{ascending:false})
 ]);
 const resumes=(resumeRows||[]) as Resume[],versions=(versionRows||[]) as Version[];
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/dashboard">← Dashboard</Link></header>
 <section className="panel"><span className="eyebrow">AI RESUME STUDIO</span><h1>Seus currículos</h1>
 <p>Crie um currículo principal e versões específicas para diferentes cargos. Revise as informações antes de aprovar.</p>
 {(resumeError||versionError)&&<p role="alert">Não foi possível carregar os currículos. Verifique a migração de dados.</p>}
 <div className="cards">{resumes.map(r=><article className="tile" key={r.id}>
 <h3>{r.title}</h3><p>{r.language==="pt-BR"?"Português":"English"}</p>
 <p>{r.summary.slice(0,180)}{r.summary.length>180?"…":""}</p>
 <small>Versões: {versions.filter(v=>v.resume_id===r.id).length}</small>
 </article>)}</div></section>
 <section className="panel"><h2>Criar currículo principal</h2>
 <p>Preencha somente experiências reais. É possível copiar as informações de um PDF exportado do LinkedIn e revisar antes de salvar.</p>
 <form className="form" action={createResume}>
 <label>Nome do currículo<input name="title" required maxLength={120} placeholder="Ex.: Projetos industriais — currículo principal"/></label>
 <label>Idioma<select name="language" defaultValue="pt-BR"><option value="pt-BR">Português</option><option value="en-US">English</option></select></label>
 <label>Resumo profissional<textarea name="summary" rows={4} maxLength={12000} placeholder="Sua trajetória e principais realizações"/></label>
 <label>Experiência profissional<textarea name="experience" rows={8} maxLength={60000} placeholder="Cargo, empresa, período, atividades e resultados comprováveis"/></label>
 <label>Competências<textarea name="skills" rows={3} maxLength={12000}/></label>
 <label>Formação e certificações<textarea name="education" rows={3} maxLength={12000}/></label>
 <button className="primary">Salvar currículo</button></form></section>
 {resumes.length>0&&<section className="panel"><h2>Versão para uma vaga</h2><p>Crie uma adaptação manual para o cargo desejado. A geração com IA e a importação automática serão conectadas posteriormente.</p>
 <form className="form" action={createVersion}>
 <label>Currículo de origem<select name="resume_id" required>{resumes.map(r=><option key={r.id} value={r.id}>{r.title}</option>)}</select></label>
 <label>Nome da versão<input name="label" maxLength={120} required placeholder="Ex.: Coordenadora de Projetos — Manufatura"/></label>
 <label>Cargo-alvo<input name="target_role" maxLength={120} placeholder="Project Coordinator"/></label>
 <label>Conteúdo revisado<textarea name="content" required rows={12} maxLength={80000}/></label>
 <button className="primary">Salvar rascunho</button></form></section>}
 {versions.length>0&&<section className="panel"><h2>Versões revisadas</h2>{versions.map(v=><article className="tile" key={v.id}>
 <h3>{v.label}</h3><p>{v.target_role} · {v.status==="approved"?"Aprovado":"Aguardando aprovação"}</p>
 <details><summary>Ler conteúdo</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{v.content}</pre></details>
 {v.status!=="approved"&&<form action={approveVersion}><input type="hidden" name="version_id" value={v.id}/><button>Aprovar versão</button></form>}
 </article>)}</section>}
 <p className="note">Esta fase não importa automaticamente o LinkedIn, não gera PDF ou DOCX e não envia candidaturas.</p></main>;
}
