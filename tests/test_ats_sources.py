import unittest
from src.ats_sources import ashby, smartrecruiters
from src.project_jobs_poc import discover


class AdditionalSourceTests(unittest.TestCase):
    def test_ashby(self):
        jobs = ashby("Employer", "employer", lambda url: {"jobs": [
            {"id": "1", "title": "Project Manager", "jobUrl": "https://example.com/1",
             "location": "Remote", "isRemote": True, "descriptionPlain": "Programs"},
            {"id": "2", "title": "Private", "jobUrl": "https://example.com/2", "isListed": False}
        ]})
        self.assertEqual(len(jobs), 1)
        self.assertTrue(jobs[0]["remote"])

    def test_smartrecruiters(self):
        jobs = smartrecruiters("Employer", "employer", lambda url: {"content": [
            {"id": "2", "name": "Project Coordinator", "ref": "https://example.com/2",
             "location": {"city": "Campinas", "country": "Brazil"},
             "releasedDate": "2026-10-17T08:00:00Z"}
        ]})
        self.assertEqual(jobs[0]["published"], "2026-10-17T08:00:00Z")
        self.assertIn("Brazil", jobs[0]["location"])

    def test_discovery_dispatch(self):
        def getter(url):
            if "ashbyhq" in url:
                return {"jobs": [{"id": "1", "title": "Project Manager",
                                 "jobUrl": "https://example.com/job", "location": "Remote"}]}
            return {"content": [{"id": "2", "name": "Project Coordinator",
                                 "ref": "https://example.com/other", "location": {}}]}
        report = discover({"boards": [
            {"source": "ashby", "company": "X", "slug": "example"},
            {"source": "smartrecruiters", "company": "Y", "slug": "example"}
        ]}, getter)
        self.assertEqual(report["total_unique"], 2)
        self.assertEqual(report["errors"], [])


if __name__ == "__main__":
    unittest.main()
