"use client";
import { useActionState } from "react";
import { previewImport, type ImportState } from "./actions";
import ReviewSections from "./ReviewSections";
const initial: ImportState = { text: "", error: "", warnings: [], filename: "" };
export default function ImportForm() {
  const [state, action, pending] = useActionState(previewImport, initial);
  return <><form action={action} className="form">
    <label>Currículo PDF ou DOCX (máximo 5 MB)<input name="resume" type="file" accept=".pdf,.docx" required /></label>
    <button className="primary" disabled={pending}>{pending ? "Analisando arquivo..." : "Extrair texto para revisão"}</button>
  </form>
  {state.error && <p role="alert">{state.error}</p>}
  {state.text && <section className="panel"><h2>Texto extraído — {state.filename}</h2>
    {state.warnings.map(w => <p className="note" key={w}>{w}</p>)}
    <p>Copie o conteúdo abaixo para o editor do currículo e organize os campos. Nada é salvo automaticamente.</p>
    <textarea readOnly value={state.text} rows={18} aria-label="Texto extraído do currículo" style={{width:"100%",padding:16,background:"#182b49",color:"white",borderRadius:12}}/>
  <h3>Organizar conteúdo para revisão</h3><ReviewSections key={state.text} text={state.text}/></section>}</>;
}
