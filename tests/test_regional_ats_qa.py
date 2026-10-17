import unittest
from src.regional_ats_qa import select


class RegionalATSTests(unittest.TestCase):
    def test_local_and_brazil_qa_only(self):
        posts = [
            {"title": "QA Automation Tester", "location": "Campinas, SP", "url": "https://jobs.lever.co/ciandt/1"},
            {"title": "Senior SDET", "location": "Brazil", "url": "https://jobs.lever.co/ciandt/2"},
            {"title": "Data Engineer", "location": "Campinas, SP", "url": "https://jobs.lever.co/ciandt/3"},
            {"title": "QA Tester", "location": "New York", "url": "https://jobs.lever.co/ciandt/4"},
        ]
        result = select(posts)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["remote_evidence"], "unknown")
        self.assertEqual(result[0]["brazil_eligible"], "unverified")


if __name__ == "__main__":
    unittest.main()
