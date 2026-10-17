import unittest
from src.linkedin_shared_links import canonical_shared_url, import_links


class SharedLinkedInTests(unittest.TestCase):
    def test_job_url_canonical(self):
        self.assertEqual(
            canonical_shared_url("https://www.linkedin.com/jobs/view/123456789/?trk=abc"),
            ("https://www.linkedin.com/jobs/view/123456789/", "job"))
    def test_post_link_is_unverified(self):
        results = import_links(["https://www.linkedin.com/posts/recruitername_projectmanager-hiring-activity-123456789"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["kind"], "post")
        self.assertEqual(results[0]["title"], "Não verificado")
    def test_reject_external_and_private_paths(self):
        self.assertEqual(import_links(["https://evil.example.com/jobs/view/123456789",
            "https://www.linkedin.com/in/person", "http://www.linkedin.com/jobs/view/123456789"]), [])
    def test_no_duplicate_and_query_removed(self):
        lines = ["https://www.linkedin.com/jobs/view/123456789/?x=1",
                 "https://www.linkedin.com/jobs/view/123456789/?x=2"]
        self.assertEqual(len(import_links(lines)), 1)


if __name__ == "__main__":
    unittest.main()
