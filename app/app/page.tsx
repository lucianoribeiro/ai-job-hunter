import { signIn } from "./actions";
export default function Home() {
  return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><span className="pill">CAREER INTELLIGENCE</span></header>
    <section className="hero"><div><span className="eyebrow">SUA CARREIRA, SEM COMPLICAÇÃO</span>
      <h1>Faça login.<br/><em>Cadastre seu CV.</em></h1>
      <p>Entre com Google, envie seu currículo em PDF com armazenamento privado e continue para o painel de vagas do AI Job Hunter.</p>
      <form action={signIn}><button className="primary">1. Entrar com Google →</button></form>
      <p className="note">2. Salvar CV privado → 3. Explorar vagas no GitHub Pages. Nenhum currículo será publicado e nenhum e-mail será enviado sem confirmação.</p>
    </div><aside className="preview"><h3>Seu painel de carreira</h3>
      <div className="tile">1. Autenticação Google</div><div className="tile">2. Upload do CV em PDF</div><div className="tile">3. Redirecionamento ao Recruiter Monitor</div>
      <small>Experiência ilustrativa — nenhuma vaga exibida até conectar fontes de dados.</small>
    </aside></section></main>;
}
