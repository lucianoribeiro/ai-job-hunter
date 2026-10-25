import unittest

from src.recruiter_monitor import indexed_contact, is_job_seeker_post


class RecruiterIndexIntegrityTests(unittest.TestCase):
    def test_seeker_post_not_a_vacancy(self):
        title = ("Open to Opportunities | Technical Lead • Lead Mobile Engineer "
                 "I am actively seeking my next role as a Technical Lead - LinkedIn")
        self.assertTrue(is_job_seeker_post(title))

    def test_real_hiring_post_not_filtered(self):
        self.assertFalse(is_job_seeker_post("We are hiring a Senior QA Engineer. Apply today."))

    def test_email_present_in_index(self):
        self.assertEqual(indexed_contact("Apply to jobs@example.com"), "jobs@example.com")

    def test_email_not_in_truncated_index_cannot_be_inferred(self):
        indexed = "Open to Opportunities | Technical Lead • Lead Mobile Engineer"
        self.assertEqual(indexed_contact(indexed), "")


if __name__ == "__main__":
    unittest.main()
