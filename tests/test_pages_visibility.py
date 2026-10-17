import unittest
from src.unified_jobs_dashboard import render

class PagesVisibilityTests(unittest.TestCase):
    def test_ai_and_honda_above_search(self):
        page = render({"jobs": []}, [], strategic={"sources": [{"company": "Honda Brasil", "state": "needs_connector"}], "jobs": []})
        self.assertIn("AI Career Studio", page)
        self.assertIn("Empresas estratégicas", page)
        self.assertLess(page.index("AI Career Studio"), page.index("Pesquisar oportunidades"))
        self.assertLess(page.index("Empresas estratégicas"), page.index("Pesquisar oportunidades"))
        self.assertIn("needs_connector", page)

    def test_unsafe_honda_title_is_escaped(self):
        page = render({"jobs": []}, [], strategic={"jobs": [{"title": "<img src=x onerror=alert(1)>", "url": "https://honda.gupy.io/jobs/123456", "company": "Honda"}]})
        self.assertIn("&lt;img", page)
        self.assertNotIn("<img src=x onerror=alert(1)>", page)
