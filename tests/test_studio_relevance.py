import unittest
from src.unified_jobs_dashboard import render, studio_job_label, studio_job_eligible

class StudioRelevanceTests(unittest.TestCase):
    def test_bilingual_title_keeps_english_role(self):
        title="[2WP] 二輪&パワースポーツ ECU プロジェクトマネジャー/ECU Project Manager for Two Wheeler & Powersports"
        self.assertEqual(studio_job_label(title), "ECU Project Manager for Two Wheeler & Powersports")

    def test_foreign_language_required_excluded_from_studio(self):
        page=render({"jobs":[
            {"title":"Software Project Manager – Japanese Speaking", "company":"Bosch Group",
             "location":"Vietnam", "url":"https://example.com/jobs/jp"},
            {"title":"Gerente de Projetos", "company":"Honda Brasil",
             "location":"Sumaré, SP", "url":"https://example.com/jobs/br"}]},[])
        options=page.split('id="aiJob"',1)[1].split("</select>",1)[0]
        self.assertIn("Gerente de Projetos",options)
        self.assertNotIn("Japanese Speaking", options)
        self.assertNotIn("jobs/jp",options)
        self.assertIn("jobs/br",options)
        self.assertIn("Software Project Manager – Japanese Speaking",page)

    def test_unknown_location_not_assumed_foreign(self):
        self.assertTrue(studio_job_eligible({"title":"Senior Project Manager","location":"","mode_key":"unknown"}))
        self.assertFalse(studio_job_eligible({"title":"Project Manager","location":"Japan","mode_key":"unknown"}))
