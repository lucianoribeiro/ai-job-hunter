import unittest
from unittest.mock import patch
from src.extra_sources import category, jobicy, collect
from src.unified_jobs_dashboard import normalize


class AdditionalSourcesTests(unittest.TestCase):
    def test_jobicy_real_api_shape(self):
        data = jobicy(lambda url: {"jobs": [
            {"jobTitle": "QA Engineer", "companyName": "ACME", "url": "https://jobicy.com/jobs/qa-1", "jobGeo": "Anywhere", "pubDate": "2026-10-16T10:00:00Z"},
            {"jobTitle": "Sales Associate", "url": "https://jobicy.com/jobs/sales"},
            {"jobTitle": "Gerente de Projetos", "companyName": "B", "url": "https://jobicy.com/jobs/projects", "jobGeo": "Brazil"}]})
        self.assertEqual(len(data), 2)
        rows = normalize({"jobs": []}, [], remote_jobs=data)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(j["source"] == "Jobicy" for j in rows))

    def test_no_key_does_not_fake_integration(self):
        with patch.dict("os.environ", {}, clear=True):
            report = collect(lambda url, *args: {"jobs": []})
            self.assertEqual(report["sources"]["Adzuna"]["status"], "credentials_required")
            self.assertEqual(report["sources"]["Jooble"]["status"], "credentials_required")

    def test_no_broad_projects_false_positives(self):
        self.assertEqual(category("Senior Project Manager"), "Projetos")
        self.assertEqual(category("QA Engineer"), "QA")
        self.assertEqual(category("Sales Associate"), "")

if __name__ == "__main__":
    unittest.main()
