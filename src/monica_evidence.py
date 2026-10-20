"""Evidence-based requirement explanation; only public vacancy phrases are exported."""
import re
from src.monica_match import COMPETENCIES, norm

def explain(job, profile):
    source = str(job.get("description") or "")
    normalized = norm(source)
    known = {norm(k) for k in profile.get("competencies", [])}
    matched, unknown = [], []
    for skill, phrases in COMPETENCIES.items():
        found = next((phrase for phrase in phrases
                      if re.search(r"(?<!\\w)"+re.escape(norm(phrase))+r"(?!\\w)", normalized)), None)
        if found is None:
            continue
        label = {"gestao de projetos":"gestão de projetos",
                 "lideranca":"liderança",
                 "cronogramas":"cronogramas",
                 "ingles":"inglês"}.get(skill, skill)
        if skill in known:
            matched.append({"requirement":label,"status":"evidence_in_cv",
                            "reason":"Competência presente no currículo e mencionada no anúncio."})
        else:
            unknown.append({"requirement":label,"status":"not_demonstrated",
                            "reason":"Requisito mencionado na vaga, sem evidência extraída do currículo."})
    if not source.strip():
        unknown.append({"requirement":"descrição completa","status":"unknown",
                        "reason":"Descrição individual da vaga não disponível; não presumir requisitos."})
    return {"matched_requirements":matched[:12],"requirements_to_confirm":unknown[:12],
            "explanation_method":"exact normalized skill phrases; not semantic AI",
            "source_has_description":bool(source.strip())}
