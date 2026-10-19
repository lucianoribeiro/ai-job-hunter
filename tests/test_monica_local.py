import tempfile
import unittest
from pathlib import Path
from src.monica_local import read_cv,structured_profile
class LocalProfileTests(unittest.TestCase):
    def test_extract_private_txt_without_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cv.txt"
            p.write_text(("Monica Ferreira: NPI, manufatura, project management, cronogramas. "*4)+"PRIVATE_EMAIL@example.com")
            text=read_cv(p)
            parsed=structured_profile(text)
            self.assertIn("npi",parsed["competencies"])
            self.assertIn("manufatura",parsed["competencies"])
            self.assertNotIn("PRIVATE_EMAIL",str(parsed))
            self.assertNotIn("Monica Ferreira",str(parsed))
    def test_reject_unknown_format(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cv.exe";p.write_text("x"*200)
            with self.assertRaises(ValueError):read_cv(p)
    def test_reject_empty_or_scanned(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"cv.txt";p.write_text("tiny")
            with self.assertRaises(ValueError):read_cv(p)
if __name__ == "__main__": unittest.main()
