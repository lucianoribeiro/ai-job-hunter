/** Draft-only message. Never claim a skill that was not confirmed in the applicant's CV. */
export function recruiterMessage(input:{title:string;company?:string;description?:string;name?:string;language?:"en"|"pt"}){
 const title=input.title.trim().slice(0,160);
 const company=(input.company||"").trim().slice(0,120);
 const detail=(input.description||"").replace(/<[^>]*>/g," ").replace(/\s+/g," ").slice(0,5000);
 const subjects=(input.language==="en")
  ?`Application – ${title}`:`Candidatura – ${title}`;
 const keywords=[["Cypress",/\bcypress\b/i],["Playwright",/\bplaywright\b/i],
  ["Selenium",/\bselenium\b/i],["automação de testes",/automati[sz]|automa[çc][aã]o/i],
  ["gestão de projetos",/project management|gest[aã]o de projetos/i],
  ["Scrum",/\bscrum\b/i],["Power BI",/power\s*bi/i]];
 const mentioned=keywords.filter(([,regex])=>(regex as RegExp).test(detail)).map(([name])=>name);
 const requirements=mentioned.length?mentioned.slice(0,4).join(", "):"os requisitos descritos no anúncio";
 const recipientName=input.name?.trim()||(input.language==="en"?"[Your name]":"[Seu nome]");
 const body=input.language==="en"
  ?`Hello,\n\nI am interested in the ${title} opportunity${company?` at ${company}`:""}. I noticed the posting mentions ${mentioned.join(", ")||"specific requirements"} and would be glad to discuss how my verified experience aligns.\n\nI have attached my resume for your consideration.\n\nBest regards,\n${recipientName}`
  :`Olá,\n\nTenho interesse na oportunidade de ${title}${company?` na ${company}`:""}. Observei que a descrição destaca ${requirements} e gostaria de conversar sobre como minhas experiências comprovadas se relacionam com esses requisitos.\n\nEncaminho meu currículo em anexo para avaliação.\n\nAtenciosamente,\n${recipientName}`;
 return {subject:subjects,body,requirements:mentioned};
}
