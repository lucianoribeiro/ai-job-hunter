import unittest
from src.hunter import classify

CONFIG = {
    "blocked_title_terms": ["sales", "recruiter"],
    "full_time_keywords": ["qa engineer", "qa manager", "test automation"],
    "freelance_keywords": ["qa", "manual tester"],
    "remote_required": True,
}

def job(**kwargs):
    data = {"title": "Senior QA Engineer", "company": "Example",
            "location": "Remote worldwide", "type": "Full time",
            "description": "Testing", "salary": "", "url": "https://example.org/job"}
    data.update(kwargs)
    return data

class StaticAuditRegressionTests(unittest.TestCase):
    def test_qa_mentioned_only_in_description_is_not_a_qa_role(self):
        self.assertIsNone(classify(job(title="Backend Developer", description="Work with QA engineer"), CONFIG))

    def test_not_remote_excluded(self):
        self.assertIsNone(classify(job(location="Not remote in Berlin"), CONFIG))

    def test_hybrid_excluded(self):
        self.assertIsNone(classify(job(location="Remote, hybrid in Berlin"), CONFIG))

    def test_remote_only_in_description_is_not_verified(self):
        self.assertIsNone(classify(job(location="Berlin", description="We collaborate with remote teams"), CONFIG))

    def test_full_time_with_contract_in_description_not_freelance(self):
        self.assertEqual(classify(job(description="Review contractor deliverables"), CONFIG)["category"], "full-time/unspecified")

    def test_explicit_contract_in_type_is_freelance(self):
        self.assertEqual(classify(job(type="Contract"), CONFIG)["category"], "freelance")

    def test_exact_two_hours_evidence(self):
        self.assertTrue(classify(job(description="2 hours per day", type="Contract"), CONFIG)["two_hours_confirmed"])

    def test_flexible_does_not_prove_two_hours(self):
        self.assertFalse(classify(job(description="Flexible schedule", type="Contract"), CONFIG)["two_hours_confirmed"])
