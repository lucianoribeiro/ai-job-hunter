import mammoth from "mammoth";
import { PDFParse } from "pdf-parse";

const MAX_BYTES = 5 * 1024 * 1024;
const MAX_TEXT = 60000;
export type ImportedResume = { extractedText: string; kind: "pdf" | "docx"; warnings: string[] };

export async function extractResume(file: File): Promise<ImportedResume> {
  if (file.size === 0 || file.size > MAX_BYTES) throw new Error("O arquivo deve ter até 5 MB.");
  const name = file.name.toLowerCase();
  const bytes = Buffer.from(await file.arrayBuffer());
  const pdf = name.endsWith(".pdf") && bytes.subarray(0, 5).toString("ascii") === "%PDF-";
  const docx = name.endsWith(".docx") && bytes.subarray(0, 2).toString("ascii") === "PK";
  if (!pdf && !docx) throw new Error("Envie um arquivo PDF ou DOCX válido.");
  let raw = "";
  if (pdf) {
    const parser = new PDFParse({ data: new Uint8Array(bytes) });
    try {
      const result = await parser.getText();
      raw = result.text;
    } finally {
      await parser.destroy();
    }
  } else {
    const result = await mammoth.extractRawText({ buffer: bytes });
    raw = result.value;
  }
  const text = raw.replace(/\r\n?/g, "\n").replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, "").trim();
  if (!text) throw new Error("Não foi possível extrair texto. PDFs digitalizados podem exigir OCR.");
  return {
    kind: pdf ? "pdf" : "docx",
    extractedText: text.slice(0, MAX_TEXT),
    warnings: [
      ...(text.length > MAX_TEXT ? ["Conteúdo limitado a 60.000 caracteres."] : []),
      "Confira cargos, empresas, períodos e resultados antes de salvar.",
    ],
  };
}
