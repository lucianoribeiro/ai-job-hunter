import unittest
from src.unified_jobs_dashboard import render, studio_seniority, studio_region

class StudioDependentFilterTests(unittest.TestCase):
    def test_seniority(self):
        self.assertEqual(studio_seniority("Senior Project Manager"),"Sênior/Liderança")
        self.assertEqual(studio_seniority("Junior QA Engineer"),"Júnior")
        self.assertEqual(studio_seniority("Project Management Intern"),"Estágio")

    def test_region(self):
        self.assertEqual(studio_region("Americana, SP","unknown"),"Região de Campinas")
        self.assertEqual(studio_region("Brazil","unknown"),"Brasil")
        self.assertEqual(studio_region("Remote - US","remote"),"Remoto (elegibilidade a verificar)")

    def test_selector_uses_actual_records_with_metadata(self):
        page=render({"jobs":[{"title":"Senior Project Manager","company":"Real Co","location":"Americana, SP","url":"https://example.com/job/42"}]},[])
        segment=page.split('id="aiJob"',1)[1].split('</select>',1)[0]
        self.assertIn('data-category="Projetos"',segment)
        self.assertIn('data-seniority="Sênior/Liderança"',segment)
        self.assertIn('data-region="Região de Campinas"',segment)
        self.assertIn('value="https://example.com/job/42"',segment)
        self.assertIn('id="studioCategory"',page)
        self.assertIn('id="studioSeniority"',page)
        self.assertIn('id="studioRegion"',page)
        self.assertIn("studioCount.textContent",page)
