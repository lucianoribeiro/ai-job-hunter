import { signIn } from "./actions";
export default function Home() {
  return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><span className="pill">CAREER INTELLIGENCE</span></header>
    <section className="hero"><div><span className="eyebrow">SUA CARREIRA, SEM COMPLICAÇÃO</span>
      <h1>Novas oportunidades.<br/><em>Mais liberdade.</em></h1>
      <p>Vagas remotas primeiro. Profissões diferentes, oportunidades personalizadas e candidaturas sob seu controle.</p>
      <form action={signIn}><button className="primary">Entrar com Google →</button></form>
      <p className="note">Seu perfil e suas candidaturas são privados. Nenhuma candidatura será enviada sem aprovação.</p>
    </div><aside className="preview"><h3>Seu painel de carreira</h3>
      <div className="tile">✦ Vagas que combinam com você</div><div className="tile">◎ Perfil e preferências personalizados</div><div className="tile">✓ Revisão de candidaturas antes do envio</div>
      <small>Experiência ilustrativa — nenhuma vaga exibida até conectar fontes de dados.</small>
    </aside></section></main>;
}
