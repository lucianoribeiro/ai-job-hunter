import Link from "next/link";
import { redirect } from "next/navigation";
import { getSupabase } from "@/lib/supabase";
import ImportForm from "./ImportForm";
export default async function ImportPage() {
  const supabase = await getSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/");
  return <main className="shell"><header className="top"><span className="logo">✦ AI Job Hunter</span><Link href="/resumes">← Resume Studio</Link></header>
    <section className="panel"><span className="eyebrow">IMPORTAÇÃO ASSISTIDA</span>
      <h1>Importar currículo</h1>
      <p>Envie um PDF exportado do LinkedIn ou seu currículo DOCX. Extrairemos o texto para conferência, sem inventar competências ou experiências.</p>
      <p className="note">Nesta etapa o arquivo é processado para uma prévia e não é armazenado. Evite documentos com dados sensíveis desnecessários.</p>
      <ImportForm />
    </section>
  </main>;
}
