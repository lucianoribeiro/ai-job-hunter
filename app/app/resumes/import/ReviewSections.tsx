"use client";
import { useMemo,useState } from "react";
import { splitResumeText } from "@/lib/resume-sections";
import { createResume } from "../actions";
export default function ReviewSections({text}:{text:string}){
 const parsed=useMemo(()=>splitResumeText(text),[text]);
 const [summary,setSummary]=useState(parsed.summary);
 const [experience,setExperience]=useState(parsed.experience);
 const [skills,setSkills]=useState(parsed.skills);
 const [education,setEducation]=useState(parsed.education);
 const [unclassified,setUnclassified]=useState(parsed.unclassified);
 return <form className="form" action={createResume}>
 <p className="note">A classificação é baseada apenas em títulos de seção reconhecidos. Nenhum dado é inventado. Revise os campos antes de salvar.</p>
 <label>Nome do currículo<input name="title" required maxLength={120} placeholder="Ex.: Currículo principal — Projetos Industriais"/></label>
 <label>Idioma<select name="language" defaultValue="pt-BR"><option value="pt-BR">Português</option><option value="en-US">English</option></select></label>
 <label>Resumo profissional<textarea name="summary" rows={5} maxLength={12000} value={summary} onChange={e=>setSummary(e.target.value)}/></label>
 <label>Experiências<textarea name="experience" rows={10} maxLength={60000} value={experience} onChange={e=>setExperience(e.target.value)}/></label>
 <label>Competências<textarea name="skills" rows={5} maxLength={12000} value={skills} onChange={e=>setSkills(e.target.value)}/></label>
 <label>Formação e certificações<textarea name="education" rows={5} maxLength={12000} value={education} onChange={e=>setEducation(e.target.value)}/></label>
 <label>Texto não classificado (não será salvo automaticamente)<textarea rows={8} value={unclassified} onChange={e=>setUnclassified(e.target.value)}/></label>
 <p className="note">Copie o texto não classificado para os campos correspondentes antes de salvar. Ele não será enviado ao banco de dados.</p>
 <button className="primary" type="submit">Revisado — salvar currículo</button>
 </form>;
}
