export type ResumeData={title:string;language:string;summary:string;experience:string;skills:string;education:string};
export function cleanPlainText(value:string,max=60000):string{
 return value.replace(/\r\n?/g,"\n").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,"").slice(0,max).trim();
}
export function resumeAsPlainText(r:ResumeData):string{
 const en=r.language==="en-US";
 const sections:[string,string][]=[
  [en?"PROFESSIONAL SUMMARY":"RESUMO PROFISSIONAL",r.summary],
  [en?"WORK EXPERIENCE":"EXPERIÊNCIA PROFISSIONAL",r.experience],
  [en?"SKILLS":"COMPETÊNCIAS",r.skills],
  [en?"EDUCATION":"FORMAÇÃO E CERTIFICAÇÕES",r.education]
 ];
 return [cleanPlainText(r.title,120).toUpperCase(),...sections.filter(([,value])=>value.trim()).map(([label,value])=>label+"\n"+cleanPlainText(value))].join("\n\n")+"\n";
}
export function escapeHtml(str:string):string{
 return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");
}
export function resumeAsAtsHtml(r:ResumeData):string {
 const en=r.language==="en-US";
 const heading=(label:string,value:string)=>value.trim()?`<section><h2>${escapeHtml(label)}</h2><p>${escapeHtml(cleanPlainText(value)).replace(/\n/g,"<br>")}</p></section>`:"";
 return `<!doctype html><html lang="${en?"en":"pt-BR"}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(r.title)} — Resume</title><style>body{font-family:Arial,Helvetica,sans-serif;color:#111;background:white;max-width:780px;margin:40px auto;padding:0 30px;line-height:1.5}h1{font-size:23px;border-bottom:2px solid #111;padding-bottom:10px}h2{font-size:14px;margin:25px 0 8px}p{font-size:12px;white-space:normal}section{break-inside:avoid}@media print{body{margin:0;max-width:initial;padding:12mm}}</style></head><body><h1>${escapeHtml(cleanPlainText(r.title,120))}</h1>${heading(en?"PROFESSIONAL SUMMARY":"RESUMO PROFISSIONAL",r.summary)}${heading(en?"WORK EXPERIENCE":"EXPERIÊNCIA PROFISSIONAL",r.experience)}${heading(en?"SKILLS":"COMPETÊNCIAS",r.skills)}${heading(en?"EDUCATION":"FORMAÇÃO E CERTIFICAÇÕES",r.education)}</body></html>`;
}
