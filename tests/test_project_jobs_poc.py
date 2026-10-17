import unittest
from src.project_jobs_poc import greenhouse, lever, discover, qualify, canonical


class SourceTests(unittest.TestCase):
    def test_greenhouse_normalization(self):
        result = greenhouse("Example", "example", lambda _: {"jobs": [{
            "id": 4, "title": "Project Manager", "absolute_url": "https://example.com/4",
            "location": {"name": "Remote"}, "content": "<p>Projects</p>", "updated_at": "2026-10-01"}]})
        self.assertEqual(result[0]["published"], None)
        self.assertEqual(result[0]["description"], "Projects")
        self.assertEqual(qualify(result[0])["remote_evidence"], "explicit")

    def test_lever_pagination_and_normalization(self):
        calls = []
        def getter(url):
            calls.append(url)
            return [{"id": "1", "text": "Project Coordinator", "hostedUrl": "https://jobs.lever.co/example/1",
                     "categories": {"location": "Brazil", "commitment": "Full-time"}}]
        result = lever("Example", "example", getter)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result[0]["employment_type"], "Full-time")
        self.assertIsNone(result[0]["published"])

    def test_deduplicate_and_title_filter(self):
        def getter(url):
            return {"jobs": [
                {"id": 1, "title": "Project Manager", "absolute_url": "https://example.com/1?a=1",
                 "location": {"name": "Campinas"}},
                {"id": 2, "title": "Project Manager", "absolute_url": "https://example.com/1?a=2",
                 "location": {"name": "Campinas"}},
                {"id": 3, "title": "Sales Manager", "absolute_url": "https://example.com/3",
                 "location": {"name": "Remote"}}]}
        report = discover({"boards": [{"source": "greenhouse", "company": "X", "slug": "example"}]}, getter)
        self.assertEqual(report["total_unique"], 1)
        self.assertEqual(report["jobs"][0]["remote_evidence"], "unknown")
        self.assertEqual(report["jobs"][0]["brazil_eligible"], "unverified")

    def test_bad_board_rejected(self):
        report = discover({"boards": [{"source": "greenhouse", "company": "X", "slug": "../secret"}]})
        self.assertEqual(len(report["errors"]), 1)

    def test_canonical_https_only(self):
        self.assertEqual(canonical("http://example.com/job"), "")
        self.assertEqual(canonical("https://example.com/job?a=1"), "https://example.com/job")

    def test_pt_titles(self):
        self.assertIsNotNone(qualify({"title": "Coordenadora de Projetos", "location": "São Paulo", "description": ""}))
        self.assertIsNone(qualify({"title": "Product Manager", "location": "Remote", "description": ""}))


if __name__ == "__main__":
    unittest.main()
