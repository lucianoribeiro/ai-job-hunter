import unittest

from src.project_jobs_poc import discover
from src.unified_jobs_dashboard import normalize


class PublishedGreenhouseIntegrationTests(unittest.TestCase):
    def test_greenhouse_qa_and_project_jobs_reach_general_opportunities(self):
        def getter(url):
            return {"jobs": [
                {"id": 101, "title": "Senior QA Engineer",
                 "location": {"name": "Brazil - Remote"},
                 "absolute_url": "https://job-boards.greenhouse.io/example/jobs/101"},
                {"id": 102, "title": "QA Manager",
                 "location": {"name": "Brazil"},
                 "absolute_url": "https://job-boards.greenhouse.io/example/jobs/102"},
                {"id": 103, "title": "QA Tech Lead",
                 "location": {"name": "Brazil"},
                 "absolute_url": "https://job-boards.greenhouse.io/example/jobs/103"},
                {"id": 104, "title": "Analista de Projetos",
                 "location": {"name": "Campinas, Brazil"},
                 "absolute_url": "https://job-boards.greenhouse.io/example/jobs/104"},
                {"id": 105, "title": "Project Manager",
                 "location": {"name": "Campinas, Brazil"},
                 "absolute_url": "https://job-boards.greenhouse.io/example/jobs/105"},
                {"id": 106, "title": "Project Coordinator",
                 "location": {"name": "Campinas, Brazil"},
                 "absolute_url": "https://job-boards.greenhouse.io/example/jobs/106"},
            ]}
        report = discover({"boards": [{"source": "greenhouse", "slug": "example", "company": "Example"}]}, getter)
        self.assertEqual(report["total_unique"], 6)
        rows = normalize(report, [])
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(row["area"] == "QA" for row in rows), 3)
        self.assertEqual(sum(row["area"] == "Projetos" for row in rows), 3)
        self.assertTrue(all(row["source"] == "Greenhouse" for row in rows))


if __name__ == "__main__":
    unittest.main()
