const b64url=(value:Uint8Array|string)=>Buffer.from(value).toString("base64").replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,"");
const header=(value:string)=>`=?UTF-8?B?${Buffer.from(value.replace(/[\r\n]+/g," "),"utf8").toString("base64")}?=`;

export function gmailDraftMime(input:{to:string;subject:string;body:string;filename:string;pdf:Uint8Array}){
 const boundary=`ai-job-hunter-${crypto.randomUUID()}`;
 const message=[
  `To: ${input.to}`,`Subject: ${header(input.subject)}`,"MIME-Version: 1.0",`Content-Type: multipart/mixed; boundary="${boundary}"`,"",
  `--${boundary}`,"Content-Type: text/plain; charset=UTF-8","Content-Transfer-Encoding: base64","",Buffer.from(input.body,"utf8").toString("base64"),
  `--${boundary}`,`Content-Type: application/pdf; name="${input.filename}"`,"Content-Transfer-Encoding: base64",`Content-Disposition: attachment; filename="${input.filename}"`,"",Buffer.from(input.pdf).toString("base64"),
  `--${boundary}--`,""
 ].join("\r\n");
 return b64url(message);
}

export async function createGmailDraft(token:string,raw:string){
 const response=await fetch("https://gmail.googleapis.com/gmail/v1/users/me/drafts",{method:"POST",headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},body:JSON.stringify({message:{raw}}),cache:"no-store"});
 if(!response.ok){const detail=await response.text();throw new Error(response.status===401||response.status===403?"Gmail authorization required":`Gmail draft failed (${response.status}): ${detail.slice(0,120)}`)}
 return response.json() as Promise<{id:string;message?:{id:string}}>;
}

/** Gmail's send endpoint returns a message id only after successful acceptance. */
export async function sendGmailMessage(token:string,raw:string){
 const response=await fetch("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",{
  method:"POST",headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},
  body:JSON.stringify({raw}),cache:"no-store"
 });
 if(!response.ok){
  const detail=await response.text();
  throw new Error(response.status===401||response.status===403?"Gmail send authorization required":`Gmail send failed (${response.status}): ${detail.slice(0,120)}`);
 }
 const result=await response.json() as {id?:string;threadId?:string};
 if(!result.id)throw new Error("Gmail did not confirm a message identifier");
 return result;
}
