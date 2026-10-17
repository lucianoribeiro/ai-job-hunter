import unittest
from unittest.mock import patch
from src.extra_sources import category, jobicy, remoteok, themuse, workable, collect
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

    def test_remoteok_skips_metadata(self):
        result = remoteok(lambda url: [{"legal": "metadata"},
            {"position":"QA Engineer","company":"Example","url":"https://remoteok.com/remote-jobs/1","date":"2026-10-17"}])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "RemoteOK")

    def test_muse_uses_landing_page(self):
        result = themuse(lambda url: {"results":[{
            "name":"Project Coordinator","company":{"name":"Example"},
            "refs":{"landing_page":"https://www.themuse.com/jobs/example/abc"},
            "locations":[{"name":"Campinas"}]}]})
        self.assertEqual(result[0]["area"], "Projetos")
        self.assertEqual(len(result), 3)  # 3 pages; one match on each mocked page

    def test_workable_requires_known_company(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(workable(lambda url: {}), ([], "boards_required"))

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
