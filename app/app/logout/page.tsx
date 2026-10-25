import Link from "next/link";
import {getSupabase} from "@/lib/supabase";
import {signOut} from "@/app/actions";

export default async function LogoutPage(){
 const supabase=await getSupabase();
 const {data:{user}}=await supabase.auth.getUser();
 const name=String(user?.user_metadata?.full_name||user?.user_metadata?.name||user?.email||"");
 return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span></header><section className="panel"><span className="eyebrow">MINHA CONTA</span><h1>Encerrar sessão</h1>{user?<><p>Usuário conectado: <strong>{name}</strong></p><p>Ao sair, sua sessão na Vercel/Supabase será encerrada. Suas vagas públicas continuam disponíveis.</p><form action={signOut}><button className="primary" type="submit">Confirmar saída e voltar ao login</button></form></>:<p>Você não possui uma sessão ativa neste navegador.</p>}<p><Link href="/">Ir para a tela de login</Link></p><p><a href="https://lucianoribeiro.github.io/ai-job-hunter/">Voltar às vagas públicas</a></p></section></main>;
}
