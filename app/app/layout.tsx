import type { ReactNode } from "react";
import "./styles.css";
export const metadata = { title: "AI Job Hunter", description: "Your career, intelligently connected." };
export default function Layout({ children }: { children: ReactNode }) {
  return <html lang="pt-BR"><body>{children}</body></html>;
}
