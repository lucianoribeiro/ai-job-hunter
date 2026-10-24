/** Canonical application origin for Google/Supabase OAuth callbacks on Vercel. */
export function applicationOrigin(){
 const configured=process.env.NEXT_PUBLIC_SITE_URL?.trim();
 const production=process.env.VERCEL_PROJECT_PRODUCTION_URL?.trim();
 const deployment=process.env.VERCEL_URL?.trim();
 const raw=configured||production||deployment;
 if(!raw)throw new Error("Configure NEXT_PUBLIC_SITE_URL or Vercel deployment domain before Google OAuth");
 const address=new URL(/^https?:\/\//.test(raw)?raw:`https://${raw}`);
 if(!["http:","https:"].includes(address.protocol)||address.username||address.password||address.pathname!=="/"||address.search||address.hash)
  throw new Error("Invalid application origin configured");
 if(address.protocol==="http:"&&!["localhost","127.0.0.1"].includes(address.hostname))
  throw new Error("Google OAuth requires HTTPS outside localhost");
 return address.origin;
}
