import unittest
from src.unified_jobs_dashboard import render

class StudioAccessibilityTests(unittest.TestCase):
    def test_accessible_live_count_and_search(self):
        html=render({"jobs":[{"title":"Gerente de Projetos","company":"Honda","location":"Sumaré","url":"https://example.org/1"}]},[])
        self.assertIn('id="studioQuery"',html)
        self.assertIn('type="search"',html)
        self.assertIn('aria-controls="aiJob"',html)
        self.assertIn('id="studioCount" role="status" aria-live="polite"',html)
        self.assertIn("studioQuery.addEventListener('input',refreshStudio)",html)
        self.assertIn("vaga encontrada",html)
        self.assertIn('Gerente de Projetos',html)

    def test_search_precedes_filters_and_results(self):
        page = render({"jobs": []}, [])
        self.assertLess(page.index('id="studioQuery"'), page.index('id="studioCategory"'))
        self.assertLess(page.index('id="studioQuery"'), page.index('id="studioCount"'))
        self.assertLess(page.index('id="studioCount"'), page.index('id="aiJob"'))
