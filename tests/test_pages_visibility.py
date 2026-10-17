import unittest
from src.unified_jobs_dashboard import render

class PagesVisibilityTests(unittest.TestCase):
    def test_ai_and_honda_above_search(self):
        page = render({"jobs": []}, [], strategic={"sources": [{"company": "Honda Brasil", "state": "needs_connector"}], "jobs": []})
        self.assertIn("AI Career Studio", page)
        self.assertIn("Vagas regionais", page)
        self.assertLess(page.index("AI Career Studio"), page.index("Pesquisar oportunidades"))
        self.assertLess(page.index("Vagas regionais"), page.index("Pesquisar oportunidades"))
        self.assertIn("needs_connector", page)

    def test_unsafe_honda_title_is_escaped(self):
        page = render({"jobs": []}, [], strategic={"jobs": [{"title": "<img src=x onerror=alert(1)>", "url": "https://honda.gupy.io/jobs/123456", "company": "Honda"}]})
        self.assertIn("&lt;img", page)
        self.assertNotIn("<img src=x onerror=alert(1)>", page)

    def test_ai_job_selector_contains_real_jobs_not_template_code(self):
        page = render({"jobs": [{"title": "Gerente de Projetos", "company": "Acme",
                                 "location": "Campinas", "url": "https://example.com/jobs/123"}]}, [])
        selection = page.split('id="aiJob"', 1)[1].split("</select>", 1)[0]
        self.assertIn("Gerente de Projetos · Acme", selection)
        self.assertIn('value="https://example.com/jobs/123"', selection)
        self.assertNotIn('j["title"]', selection)
        self.assertNotIn('__AI_JOB_OPTIONS__', selection)
        self.assertIn('Selecionar uma vaga do catálogo...', selection)
