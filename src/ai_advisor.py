"""Generate an evidence-first advisory summary from stored job metadata."""
import json
from datetime import datetime, timezone
from src.hunter import DATA

def summarize(queue):
    jobs = sorted((j for j in queue.values() if isinstance(j, dict) and j.get("status") not in ("dismissed", "rejected")), key=lambda j: -int(j.get("score") or 0))
    recommended = []
    for job in jobs[:3]:
        assessment = job.get("assessment") or {}
        reasons = assessment.get("fit_reasons") or []
        recommended.append({"title": job.get("title", ""), "company": job.get("company", ""),
                            "url": job.get("url", ""), "score": job.get("score", 0),
                            "reason": "; ".join(reasons) or "Compatibilidade preliminar: validar requisitos."})
    return {"mode": "rules", "headline": "Seu radar inteligente de oportunidades",
            "summary": "Ranking preliminar por critérios objetivos. A avaliação por modelo de IA ainda não está configurada. Confirme reputação da empresa, elegibilidade no Brasil, remuneração em USD e horas disponíveis.",
            "recommendations": recommended, "generated_at": datetime.now(timezone.utc).isoformat()}

def run():
    path = DATA / "applications.json"
    queue = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(queue, dict):
        raise ValueError("Queue must be a JSON object")
    DATA.mkdir(exist_ok=True)
    (DATA / "ai_insights.json").write_text(json.dumps(summarize(queue), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    run()
