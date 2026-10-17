import { redirect } from "next/navigation";
import Link from "next/link";
import { createCareerProfile, signOut } from "../actions";
import { getSupabase } from "@/lib/supabase";

type Profile = { id: string; label: string; industry: string; target_roles: string[]; origin_city: string; max_radius_km: number; include_hybrid: boolean };
export default async function Dashboard() {
  const supabase = await getSupabase();
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) redirect("/");
  const { data, error: dbError } = await supabase.from("career_profiles").select("id,label,industry,target_roles,origin_city,max_radius_km,include_hybrid").order("created_at", { ascending: false });
  const profiles = (data || []) as Profile[];
  return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><form action={signOut}><button>Encerrar sessão</button></form></header>
    <section className="panel"><div className="controls"><Link href="/jobs">Explorar vagas recentes →</Link><Link href="/applications">Minhas candidaturas →</Link><Link href="/resumes">Meus currículos →</Link></div><span className="eyebrow">MEU ESPAÇO</span><h1>Minha carreira</h1><p>Configure seu perfil e suas preferências para encontrar oportunidades relevantes.</p>
    {dbError && <p role="alert">Não foi possível carregar seus perfis. Verifique a configuração do banco.</p>}
    <div className="cards">{profiles.map(p => <article className="tile" key={p.id}><h3>{p.label}</h3><p>{p.industry || "Setor não informado"}</p><p>{p.target_roles.join(" · ")}</p><small>Remoto primeiro {p.include_hybrid ? `· híbrido até ${p.max_radius_km} km` : ""}{p.origin_city ? ` · ${p.origin_city}` : ""}</small></article>)}</div>
    </section>
    <section className="panel"><h2>Adicionar perfil profissional</h2><p>Você pode criar perfis para diferentes carreiras e setores.</p>
      <form action={createCareerProfile} className="form">
        <label>Nome do perfil<input required name="label" maxLength={120} placeholder="Ex.: Projetos industriais"/></label>
        <label>Setor<input name="industry" maxLength={120} placeholder="Ex.: Manufatura"/></label>
        <label>Cargos de interesse (separados por vírgula)<input required name="roles" placeholder="Gerente de Projetos, Coordenadora de Projetos"/></label>
        <label>Cidade de referência<input name="city" maxLength={120} placeholder="Nova Odessa, SP"/></label>
        <label>Raio máximo (km)<input name="radius" type="number" min="0" max="500" defaultValue="50"/></label>
        <label className="check"><input name="hybrid" type="checkbox"/> Considerar híbrido/presencial dentro do raio</label>
        <button className="primary">Salvar perfil</button>
      </form>
    </section><p className="note">Explore vagas e acompanhe candidaturas com revisão humana. Não publique currículos no repositório.</p>
  </main>;
}
