"""Evidence-based project/NPI CV-to-vacancy matching. Never store private CV text in public outputs."""
from __future__ import annotations
import re
import unicodedata
from urllib.parse import urlsplit

ROLE_TERMS = ("gerente de projetos", "coordenador de projetos", "coordenadora de projetos",
              "project manager", "project coordinator", "npi", "program manager",
              "program coordinator", "pmo coordinator", "especialista de projetos")
EXCLUDE_ROLES = ("coordenador de producao", "gerente de producao", "production supervisor",
                 "production manager", "engenheiro eletricista", "electrical engineer")
COMPETENCIES = {
    "gestao de projetos": ("gestao de projetos", "project management", "project manager"),
    "npi": ("npi", "new product introduction", "introducao de novos produtos"),
    "manufatura": ("manufacturing", "manufatura", "industrial", "factory"),
    "cronogramas": ("schedule", "scheduling", "cronograma", "timeline"),
    "riscos": ("risk management", "gestao de riscos", "riscos"),
    "stakeholders": ("stakeholder", "clientes", "customer"),
    "lideranca": ("leadership", "lideranca", "gestao de equipes", "team management"),
    "ms project": ("ms project", "microsoft project"),
    "power bi": ("power bi",),
    "scrum": ("scrum", "agile"),
    "ingles": ("english", "ingles"),
}
CLOSED = (r"nao aceita mais candidaturas", r"no longer accepting applications",
          r"applications? (?:are )?closed", r"job (?:is )?expired", r"vaga encerrada",
          r"position (?:has been )?filled")
REGIONAL = ("campinas", "jaguariuna", "hortolandia", "sumare", "paulinia",
            "americana", "nova odessa", "indaiatuba")

def norm(value):
    text = unicodedata.normalize("NFKD", str(value or "").lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))

def application_status(page_text, source_verified=False):
    """A listing/search snippet cannot prove an application remains available."""
    text = norm(page_text)
    if any(re.search(p, text) for p in CLOSED):
        return "closed"
    if source_verified and re.search(r"\b(apply (now|for this job)|candidate-se|candidatar-se)\b", text):
        return "apply_indicated"
    return "unverified"

def assess(job, profile, page_text="", source_verified=False):
    """Return only public, explainable job metadata. profile is never returned."""
    title = norm(job.get("title"))
    description = norm(job.get("description") or page_text)
    location = norm(job.get("location"))
    combined = title + " " + description
    evidence, gaps = [], []
    valid_role = any(term in title for term in ROLE_TERMS)
    irrelevant = any(term in title for term in EXCLUDE_ROLES)
    expected = {norm(v) for v in profile.get("competencies", [])}
    matches = [key for key, synonyms in COMPETENCIES.items()
               if key in expected and any(term in combined for term in synonyms)]
    for key in matches:
        evidence.append("Requisito relacionado a experiência comprovada: " + key)
    for required, patterns in {
        "Engenharia": ("graduacao em engenharia", "degree in engineering", "engineering degree"),
        "MES/ERP": ("mes experience required", "experiencia obrigatoria em mes"),
        "projetos de software": ("software development experience required",)
    }.items():
        if any(p in combined for p in patterns) and norm(required) not in expected:
            gaps.append("Requisito a confirmar: " + required)
    remote = any(t in (location + " " + description) for t in ("remoto", "remote", "work from home"))
    regional = any(t in location for t in REGIONAL)
    if not remote and not regional:
        gaps.append("Localização ou elegibilidade regional não confirmada")
    status = application_status(page_text, source_verified)
    if status == "closed":
        gaps.append("Candidatura encerrada: não exibir nos alertas ativos")
    elif status == "unverified":
        gaps.append("Status da candidatura não verificado")
    if not job.get("url") or urlsplit(str(job.get("url"))).scheme not in ("http", "https"):
        gaps.append("URL de candidatura inválida")
    # Rank the professional match; do not penalize a vacancy merely because
    # its public application page could not be checked. Status is a separate axis.
    technical_gaps = sum(g.startswith("Requisito a confirmar:") for g in gaps)
    score = max(0, min(100, 35 + len(matches)*12 + (10 if valid_role else -30)
                    + (10 if remote or regional else 0) - technical_gaps*12
                    - (50 if irrelevant else 0)))
    return {
        "title": str(job.get("title") or ""), "company": str(job.get("company") or ""),
        "location": str(job.get("location") or ""), "url": str(job.get("url") or ""),
        "source": str(job.get("source") or ""), "profile_id": str(profile.get("id") or "monica"),
        "application_status": status, "score": score,
        "matches": matches, "evidence": evidence, "gaps": gaps,
        "recommendation": ("exclude" if status == "closed" or irrelevant or not valid_role
                            else "review" if status != "apply_indicated" or gaps
                            else "recommended" if score >= 70 else "review"),
        "note": "Pontuação heurística de aderência, não probabilidade de contratação.",
    }
