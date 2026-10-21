/**
 * Extract only explicit, syntactically valid email addresses from the supplied
 * public job description. This does not infer or guess recruiter addresses.
 */
export function recruiterEmails(description:string):string[]{
 const normalized=description.replace(/&#64;|&commat;/gi,"@").replace(/\s+\[at\]\s+/gi,"@").replace(/\s+\(at\)\s+/gi,"@");
 const matches=normalized.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi)||[];
 const blocked=/^(?:noreply|no-reply|donotreply|do-not-reply|privacy|abuse|security|support|help|info)@/i;
 return Array.from(new Set(matches.map(m=>m.toLowerCase()).filter(m=>m.length<=254&&!blocked.test(m)))).slice(0,5);
}
