import tempfile
import unittest
from pathlib import Path
from src.linkedin_alerts import canonical_job_url, extract_eml, import_files


class LinkedInAlertsTests(unittest.TestCase):
    def test_canonicalizes_and_strips_tracking(self):
        self.assertEqual(canonical_job_url("https://www.linkedin.com/jobs/view/12345678/?trk=email"),
                         "https://www.linkedin.com/jobs/view/12345678/")
        self.assertIsNone(canonical_job_url("https://evil.com/jobs/view/12345678"))
        self.assertIsNone(canonical_job_url("javascript:alert(1)"))

    def test_parses_without_exporting_email_identity(self):
        source = (b"From: secret.person@example.com\nTo: another@example.com\n"
                  b"Subject: Job alert\nMIME-Version: 1.0\nContent-Type: text/html; charset=utf-8\n\n"
                  b'<a href="https://www.linkedin.com/jobs/view/12345678/?trk=eml">QA Engineer</a>')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.eml"
            path.write_bytes(source)
            jobs = import_files([path])
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["title"], "QA Engineer")
            self.assertNotIn("secret.person", str(jobs))
            self.assertFalse(jobs[0]["remote"])

    def test_duplicate_links(self):
        source = (b"Content-Type: text/html; charset=utf-8\n\n"
                  b'<a href="https://linkedin.com/jobs/view/12345678">QA</a>'
                  b'<a href="https://linkedin.com/jobs/view/12345678?trk=a">QA again</a>')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.eml"
            path.write_bytes(source)
            self.assertEqual(len(extract_eml(path)), 1)


if __name__ == "__main__":
    unittest.main()
