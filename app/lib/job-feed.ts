export type JobListing = {id:string;title:string;company:string;url:string;location:string;published:string;remote:boolean;source:string;description:string};
function text(value:unknown){return String(value??"").replace(/<[^>]*>/g," ").replace(/&amp;/g,"&").replace(/\s+/g," ").trim().slice(0,4000)}
function validHttp(url:string){try{const u=new URL(url);return u.protocol==="https:"?u.toString():""}catch{return ""}}
export async function fetchRecentJobs():Promise<{jobs:JobListing[];warnings:string[]}>{
 const warnings:string[]=[];const gathered:JobListing[]=[];
 const feeds=[
  {name:"Remotive",url:"https://remotive.com/api/remote-jobs?limit=100"},
  {name:"Arbeitnow",url:"https://www.arbeitnow.com/api/job-board-api"}
 ];
 await Promise.all(feeds.map(async f=>{
  try{
   const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),8500);
   let json:unknown;
   try{const response=await fetch(f.url,{signal:controller.signal,next:{revalidate:900},headers:{"Accept":"application/json"}});
    if(!response.ok)throw new Error("HTTP "+response.status);json=await response.json();}
   finally{clearTimeout(timer)}
   const body=json as Record<string,unknown>;
   const rows=f.name==="Remotive" ? body.jobs : body.data;
   if(!Array.isArray(rows)) throw new Error("unexpected response");
   for(const value of rows.slice(0,150)){
    if(!value||typeof value!=="object")continue;
    const j=value as Record<string,unknown>;
    const url=validHttp(String(j.url??""));if(!url)continue;
    const remote=f.name==="Remotive"||j.remote===true;
    gathered.push({
     id:f.name+":"+String(j.id??j.slug??url).slice(0,180),
     title:text(j.title).slice(0,200),company:text(j.company_name).slice(0,160),
     url,location:text(f.name==="Remotive"?j.candidate_required_location:j.location).slice(0,160),
     published:publishedDate(f.name==="Remotive"?j.publication_date:j.created_at),
     remote,source:f.name,description:text(j.description)
    });
   }
  }catch{warnings.push("Fonte indisponível temporariamente: "+f.name)}
 }));
 const unique=new Map<string,JobListing>();
 for(const job of gathered)if(job.title&&!unique.has(job.url))unique.set(job.url,job);
 return {jobs:[...unique.values()].sort((a,b)=>b.published.localeCompare(a.published)).slice(0,200),warnings};
}
function publishedDate(value:unknown):string{
 if(typeof value==="number"){const ms=value<1e11?value*1000:value;const d=new Date(ms);return Number.isFinite(d.valueOf())?d.toISOString():"";}
 if(typeof value==="string"){const d=new Date(value);return Number.isFinite(d.valueOf())?d.toISOString():"";}
 return "";
}
export function matchingJobs(jobs:JobListing[],roles:string[],onlyRemote:boolean):JobListing[]{
 const terms=roles.map(x=>x.trim().toLowerCase()).filter(Boolean);
 return jobs.filter(j=>(!onlyRemote||j.remote)&&(!terms.length||terms.some(t=>{
  const words=t.split(/\s+/).filter(x=>x.length>=3);
  const haystack=(j.title+" "+j.description.slice(0,1200)).toLowerCase();
  return words.length>0&&words.every(w=>haystack.includes(w));
 })));
}
