import unittest
from unittest.mock import patch
from src import public_sources as s

class PublicSourceTests(unittest.TestCase):
    def test_slug_validation(self):
        self.assertEqual(s.slug("acme-inc"), "acme-inc")
        for value in ("../private", "x/y", "https://example.com", ""):
            with self.assertRaises(ValueError):
                s.slug(value)

    @patch.object(s, "get")
    def test_greenhouse_mapping(self, get):
        get.return_value = {"jobs": [{"id": 123, "title": "QA Engineer", "absolute_url": "https://example.com/123",
                                      "location": {"name": "Campinas"}, "first_published": "2026-10-01"}]}
        job = s.greenhouse("Acme", "acme")[0]
        self.assertEqual(job["company"], "Acme")
        self.assertEqual(job["published"], "2026-10-01")
        self.assertEqual(job["source"], "Greenhouse")

    @patch.object(s, "get")
    def test_lever_mapping(self, get):
        get.return_value = [{"id": "123", "text": "QA Lead", "hostedUrl": "https://example.com",
                             "categories": {"location": "Remote", "commitment": "Contract"}}]
        self.assertEqual(s.lever("Acme", "acme")[0]["type"], "Contract")

    @patch.object(s, "get")
    def test_ashby_mapping(self, get):
        get.return_value = {"jobs": [{"id": "1", "title": "QA Manager", "jobUrl": "https://example.com",
                                      "isRemote": True, "isListed": True},
                                     {"id": "2", "title": "Hidden", "isListed": False}]}
        jobs = s.ashby("Acme", "acme")
        self.assertEqual(len(jobs), 1)
        self.assertTrue(jobs[0]["remote"])

    def test_empty_boards_make_no_requests(self):
        self.assertEqual(s.collect_boards({"company_boards": {"greenhouse": []}}), ([], []))

if __name__ == "__main__":
    unittest.main()
