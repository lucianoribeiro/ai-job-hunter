import unittest
from src.unified_jobs_dashboard import render

class StudioAccessibilityTests(unittest.TestCase):
    def test_accessible_live_count_without_search(self):
        page = render({"jobs":[{"title":"Gerente de Projetos","company":"Honda","location":"Sumaré","url":"https://example.org/1"}]},[])
        self.assertNotIn('id="studioQuery"', page)
        self.assertIn('id="studioCount" role="status" aria-live="polite"', page)
        self.assertIn("studioCategory",page)
        self.assertIn("studioSeniority",page)
        self.assertIn("studioRegion",page)
        self.assertIn("vaga encontrada",page)
        self.assertIn("Gerente de Projetos",page)

    def test_filters_precede_count_and_selector(self):
        page = render({"jobs":[]},[])
        self.assertLess(page.index('id="studioCategory"'),page.index('id="studioCount"'))
        self.assertLess(page.index('id="studioCount"'),page.index('id="aiJob"'))
