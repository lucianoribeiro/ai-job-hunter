import {PDFDocument,StandardFonts,rgb} from "pdf-lib";
import {cleanPlainText} from "./resume-export";

const wrap=(text:string,max=92)=>{
 const words=text.split(/\s+/), lines:string[]=[];let line="";
 for(const word of words){const next=line?`${line} ${word}`:word;if(next.length>max&&line){lines.push(line);line=word}else line=next}
 if(line)lines.push(line);return lines;
};

export async function professionalResumePdf(content:string,title="Professional Resume"):Promise<Uint8Array>{
 const pdf=await PDFDocument.create(),regular=await pdf.embedFont(StandardFonts.Helvetica),bold=await pdf.embedFont(StandardFonts.HelveticaBold);
 const margin=48,width=595,height=842;let page=pdf.addPage([width,height]),y=height-margin;
 const addPage=()=>{page=pdf.addPage([width,height]);y=height-margin};
 const draw=(text:string,size=10,isBold=false,color=rgb(.12,.16,.22))=>{
  if(y<margin+size*2)addPage();page.drawText(text,{x:margin,y,size,font:isBold?bold:regular,color});y-=size+5;
 };
 draw(cleanPlainText(title,120),20,true,rgb(.06,.24,.32));y-=4;
 page.drawLine({start:{x:margin,y},end:{x:width-margin,y},thickness:1.5,color:rgb(.12,.55,.52)});y-=18;
 for(const raw of cleanPlainText(content,80000).split("\n")){
  const line=raw.trim();if(!line){y-=6;continue}
  const heading=line.length<55&&(line===line.toUpperCase()||/^(summary|experience|skills|education|certifications|languages|resumo|experiência|competências|formação|certificações|idiomas)/i.test(line));
  if(heading){y-=4;draw(line.replace(/:$/,"").toUpperCase(),11,true,rgb(.06,.24,.32));continue}
  for(const part of wrap(line.replace(/^[•*-]\s*/,"• ")))draw(part,9.5,false);
 }
 pdf.setTitle(title);pdf.setCreator("AI Job Hunter");pdf.setProducer("AI Job Hunter");
 return pdf.save();
}

export function safeResumeFilename(role:string){
 const slug=role.normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/gi,"_").replace(/^_|_$/g,"").slice(0,70)||"Professional_CV";
 return `CV_${slug}.pdf`;
}
