/** Editable recruiter drafts: only claim verified experience, never invent email addresses. */
export const CANDIDATE_LINKEDIN = "https://www.linkedin.com/in/luciano-ribeiro-0321a46b/";
export function vacancyTitle(raw:string):string {
 // A recruiter post headline is often the full post, not the actual job title.
 const text=raw.replace(/<[^>]*>/g," ").replace(/&(?:nbsp|amp);/gi," ")
  .replace(/\\s+-\\s+LinkedIn\\s*$/i,"").replace(/^[\\s🚀📢🔥📣💼🔎]+/u,"")
  .replace(/^\\s*(?:#?hiring|#?wearehiring|now hiring|urgent hiring)\\b\\s*[:–—-]?\\s*/i,"")
  .replace(/\\s+/g," ").trim();
 const clean=text.split(/\\s+(?:(?:experience|exp|job\\s*type|employment\\s*type|location|work\\s*mode|salary|notice\\s*period|duration|apply\\s*at|email|contact)\\s*[:：]|\\d{1,2}\\s*[-–]\\s*\\d{1,2}\\s*(?:yrs?|years?)\\b)/i)[0]
  .replace(/\\s*(?:[|•–—]\\s*)?(?:#?hiring|apply now)\\s*$/i,"").trim();
 const known=clean.match(/\\b(Senior Executive\\s*[–-]\\s*Quality Assurance(?:\\s*\\([^)]{1,40}\\))?|Senior QA Automation Engineer|QA Automation Lead|QA Automation Engineer|AEM\\s+QA(?:\\s+Workfront)?|QA\\s+Workfront|Quality Engineer|Software Development Engineer in Test|SDET|Technical Project Manager|Project Manager|QA Engineer)(?=\\s|$|[.,!])/i);
 if(known)return known[1].trim().slice(0,90);
 const role=clean.match(/(?:looking for|hiring for|position:|job title:|role:)\\s+(?:an?\\s+)?(.{4,85}?)(?=\\s+(?:to join|with|at|in|who|for our|location:|experience:)|[.!?]|$)/i);
 if(role)return role[1].trim().slice(0,90);
 const fallback=(clean.split(/[.!?]|\\s+(?:to join|interested candidates)\\b/i)[0]||"").trim();
 // A long sentence is not a job title: avoid sending an unprofessional subject.
 return fallback && fallback.length<=75 ? fallback : "QA Opportunity";
}
export function vacancyLanguage(title:string,description=""): "en"|"pt" {
 const text=(title+" "+description).toLowerCase();
 const en=(text.match(/\b(we.re|we are|hiring|looking for|join our|candidates|experience|required|skills|position|interested|apply|job|team)\b/g)||[]).length;
 const pt=(text.match(/\b(vaga|contratando|candidatura|experiência|requisitos|oportunidade|inscreva|remoto|procuramos|estamos|seleção|equipe|currículo)\b/g)||[]).length;
 return en>pt?"en":pt>en?"pt":/\b(?:we.re|hiring|looking for)\b/i.test(text)?"en":"pt";
}
export function recruiterMessage(input:{title:string;company?:string;description?:string;name?:string;language?:"en"|"pt"}){
 const role=vacancyTitle(input.title), detail=(input.description||"").replace(/<[^>]*>/g," ").replace(/\s+/g," ").slice(0,5000);
 const lang=input.language||vacancyLanguage(input.title,detail), company=(input.company||"").trim().slice(0,120);
 const subject=((lang==="en"?"Application – ":"Candidatura – ")+role).slice(0,250);
 const skills=[["Cypress",/\bcypress\b/i],["Playwright",/\bplaywright\b/i],["Selenium",/\bselenium\b/i],["mobile testing",/\bmobile\b/i],["project management",/\bproject management\b/i],["Scrum",/\bscrum\b/i]].filter(([,re])=>(re as RegExp).test(detail)).map(([label])=>label).slice(0,3);
 const name=input.name?.trim()||(lang==="en"?"[Your name]":"[Seu nome]");
 const opening=lang==="en"?"Hello,":"Olá,";
 const intro=lang==="en"?"I am writing to express my interest in the "+role+" position"+(company?" at "+company:"")+".":"Gostaria de demonstrar meu interesse na vaga de "+role+(company?" na "+company:"")+".";
 const context=lang==="en"?(skills.length?"The posting mentions "+skills.join(", ")+". I would welcome a discussion about how my background relates to these requirements.":"I would welcome an opportunity to discuss how my experience relates to the position."):(skills.length?"A publicação menciona "+skills.join(", ")+". Gostaria de conversar sobre como minha experiência se relaciona com esses requisitos.":"Gostaria de conversar sobre como minha experiência se relaciona com os requisitos desta oportunidade.");
 const closing=lang==="en"?"Please find my resume attached for your consideration.":"Encaminho meu currículo em anexo para avaliação.";
 const sign=lang==="en"?"Best regards,":"Atenciosamente,";
 return {subject,body:[opening,"",intro+" "+context,"",closing,"LinkedIn: "+CANDIDATE_LINKEDIN,"",sign,name].join("\n"),requirements:skills};
}
