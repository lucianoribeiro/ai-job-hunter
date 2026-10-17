"""Evidence-based QA opportunity assessment. Unknown signals are not assumed positive."""
import re

SKILLS = ("selenium", "playwright", "cypress", "pytest", "api testing", "automation",
          "shift-left", "ci/cd", "leadership", "test strategy", "llm", "ai testing")

def assess_opportunity(job, profile_text=""):
    title = str(job.get("title") or "").lower()
    location = str(job.get("location") or "").lower()
    salary = str(job.get("salary") or "")
    category = str(job.get("category") or "")
    evidence = []
    warnings = []
    if re.search(r"\\b(qa|quality assurance|quality engineer|sdet|software tester|test automation)\\b", title):
        evidence.append("Cargo relacionado a QA")
    if re.search(r"\\b(manager|lead|head|principal)\\b", title):
        evidence.append("Potencial de liderança")
    usd = bool(re.search(r"\\bUSD\\b|US\\$", salary, re.I))
    if usd:
        evidence.append("Remuneração em USD indicada")
    else:
        warnings.append("Moeda não confirmada em USD")
    brasil = bool(re.search(r"\\b(brazil|brasil|worldwide|anywhere|global)\\b", location))
    if brasil:
        evidence.append("Localização potencialmente compatível; confirmar regras da empresa")
    else:
        warnings.append("Elegibilidade para residentes no Brasil não verificada")
    if category == "freelance":
        evidence.append("Contrato flexível potencial: confirmar carga horária")
        if not job.get("two_hours_confirmed", False) in (True, "True"):
            warnings.append("Disponibilidade de até 2h/dia não confirmada")
    warnings.append("Reputação e estabilidade da empresa ainda não verificadas")
    text = profile_text.lower()
    matching = [skill for skill in SKILLS if skill in text and skill in (title + " " + str(job.get("description") or "").lower())]
    if matching:
        evidence.append("Competências coincidentes: " + ", ".join(matching[:5]))
    score = min(100, len(evidence) * 12 + len(matching) * 5)
    return {"evidence": evidence, "warnings": warnings, "skills_matched": matching, "evidence_score": score,
            "company_quality": "unverified", "brazil_eligibility": "needs_review"}
