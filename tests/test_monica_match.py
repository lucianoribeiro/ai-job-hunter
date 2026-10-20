import unittest
from src.monica_match import assess, application_status
PROFILE = {"id": "monica", "competencies": ["npi", "manufatura", "gestao de projetos", "cronogramas", "lideranca"]}
JOB = {"title": "Coordenadora de Projetos NPI", "company": "Test company",
       "description": "Projetos NPI na manufatura, gestão de cronogramas e liderança",
       "location": "Campinas, SP", "url": "https://example.com/job"}
class MonicaMatchTests(unittest.TestCase):
    def test_closed_accented(self):
        self.assertEqual(application_status("Não aceita mais candidaturas", True), "closed")
    def test_unverified_link_is_not_open(self):
        self.assertEqual(application_status("Apply now", False), "unverified")
    def test_indicated_form(self):
        self.assertEqual(application_status("Apply now", True), "apply_indicated")
    def test_cv_is_not_leaked(self):
        profile = {**PROFILE, "secret": "PRIVATE_CV_BODY"}
        result = assess(JOB, profile, "Apply now", True)
        self.assertNotIn("PRIVATE_CV_BODY", str(result))
        self.assertEqual(result["profile_id"], "monica")
        self.assertIn("npi", result["matches"])
    def test_non_project_role_excluded(self):
        result = assess({**JOB, "title": "Coordenador de Produção"}, PROFILE, "Apply now", True)
        self.assertEqual(result["recommendation"], "exclude")
    def test_closed_never_recommended(self):
        result = assess(JOB, PROFILE, "Não aceita mais candidaturas", True)
        self.assertEqual(result["recommendation"], "exclude")
if __name__ == "__main__":
    unittest.main()
