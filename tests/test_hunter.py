import unittest
from src.hunter import classify, plain


CONFIG = {
    "blocked_title_terms": ["sales", "recruiter"],
    "full_time_keywords": ["qa engineer", "qa manager", "test automation"],
    "remote_required": True,
}


def job(**changes):
    value = {"title": "Senior QA Engineer", "company": "Acme", "url": "https://example.com/job",
             "location": "Remote worldwide", "salary": "USD 60/hour",
             "type": "Contract", "description": "Flexible project", "source": "Test"}
    value.update(changes)
    return value


class RankingTests(unittest.TestCase):
    def test_contract_usd(self):
        result = classify(job(), CONFIG)
        self.assertEqual(result["category"], "freelance")
        self.assertTrue(result["usd_confirmed"])
        self.assertFalse(result["two_hours_confirmed"])

    def test_non_remote_rejected(self):
        self.assertIsNone(classify(job(location="Berlin", description="Onsite", type="Full time"), CONFIG))

    def test_unrelated_role_rejected(self):
        self.assertIsNone(classify(job(title="Sales Director"), CONFIG))

    def test_html_cleanup(self):
        self.assertEqual(plain("<p>QA &amp; testing</p>"), "QA & testing")


if __name__ == "__main__":
    unittest.main()
