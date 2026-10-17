/** Prepare a Gmail compose URL. Opening it does NOT send, attach or persist a draft. */
export function gmailComposeUrl(recipient:string,subject:string,body:string):string{
 const url=new URL("https://mail.google.com/mail/u/0/");
 url.searchParams.set("view","cm");
 url.searchParams.set("fs","1");
 url.searchParams.set("to",recipient);
 url.searchParams.set("su",subject);
 url.searchParams.set("body",body);
 return url.toString();
}
