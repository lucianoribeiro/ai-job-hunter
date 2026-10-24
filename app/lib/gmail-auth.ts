/** Check Google OAuth authorization without storing or logging tokens. */
export async function gmailAuthorization(token?:string|null){
 if(!token)return {connected:false,canCompose:false,canSend:false,reason:"not_connected"} as const;
 try{
  const response=await fetch("https://www.googleapis.com/oauth2/v3/tokeninfo?access_token="+encodeURIComponent(token),{cache:"no-store"});
  if(!response.ok)return {connected:false,canCompose:false,canSend:false,reason:"expired"} as const;
  const data=await response.json() as {scope?:string;expires_in?:string};
  const scopes=new Set((data.scope||"").split(/\s+/).filter(Boolean));
  const canCompose=scopes.has("https://www.googleapis.com/auth/gmail.compose")||scopes.has("https://mail.google.com/");
  const canSend=scopes.has("https://www.googleapis.com/auth/gmail.send")||scopes.has("https://mail.google.com/");
  return {connected:canCompose||canSend,canCompose,canSend,reason:canSend?"ok":"missing_scope"} as const;
 }catch{
  return {connected:false,canCompose:false,canSend:false,reason:"verification_unavailable"} as const;
 }
}
