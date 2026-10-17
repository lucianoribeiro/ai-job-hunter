import unittest
from src.recruiter_outreach import candidates, create_draft

POST = "We are hiring a remote QA Engineer. Please send your CV to jobs@example.com to apply."
PROFILE = {"name": "Applicant", "strengths": ["test automation", "QA leadership"]}


class OutreachTests(unittest.TestCase):
    def test_explicit_application_email(self):
        found = candidates(POST)
        self.assertEqual(found[0]["email"], "jobs@example.com")
        self.assertTrue(found[0]["needs_human_verification"])

    def test_email_alone_not_enough(self):
        self.assertEqual(candidates("QA manager conference. Contact me at person@example.com."), [])

    def test_unrelated_post_not_accepted(self):
        self.assertEqual(candidates("Hiring designer. Send resume to jobs@example.com"), [])

    def test_draft_requires_review(self):
        draft = create_draft(POST, "jobs@example.com", PROFILE, "resume.pdf")
        self.assertFalse(draft["send_allowed"])
        self.assertEqual(draft["status"], "requires_review")
        self.assertIn("resume.pdf", draft["attachment_to_add"])

    def test_unadvertised_recipient_rejected(self):
        with self.assertRaises(ValueError):
            create_draft(POST, "other@example.com", PROFILE, "resume.pdf")


if __name__ == "__main__":
    unittest.main()
