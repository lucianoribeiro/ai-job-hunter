export type ResumeSections = { summary:string; experience:string; skills:string; education:string; unclassified:string };
const RULES: {key:Exclude<keyof ResumeSections,"unclassified">;pattern:RegExp}[]=[
 {key:"summary",pattern:/^(?:resumo(?: profissional)?|perfil profissional|sobre mim|professional summary|profile|about me|objective|objetivo(?: profissional)?)\s*:?[ \t]*$/i},
 {key:"experience",pattern:/^(?:experi[eê]ncia(?: profissional)?|hist[oó]rico profissional|work experience|professional experience|employment history|career history)\s*:?[ \t]*$/i},
 {key:"skills",pattern:/^(?:compet[eê]ncias|habilidades|conhecimentos|skills|core competencies|technical skills)\s*:?[ \t]*$/i},
 {key:"education",pattern:/^(?:forma[cç][aã]o(?: acad[eê]mica)?|educa[cç][aã]o|certifica[cç][oõ]es|education|certifications|academic background)\s*:?[ \t]*$/i}
];
export function splitResumeText(text:string):ResumeSections{
 const result:ResumeSections={summary:"",experience:"",skills:"",education:"",unclassified:""};
 let active:keyof ResumeSections="unclassified";
 for(const raw of text.replace(/\r\n?/g,"\n").split("\n")){
   const line=raw.trim();
   const section=RULES.find(rule=>rule.pattern.test(line));
   if(section){active=section.key;continue;}
   if(!line && !result[active])continue;
   result[active]+=(result[active]?"\n":"")+raw;
 }
 for(const key of Object.keys(result) as (keyof ResumeSections)[]) result[key]=result[key].trim();
 return result;
}
