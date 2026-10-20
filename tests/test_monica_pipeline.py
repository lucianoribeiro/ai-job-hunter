import unittest
from src.monica_pipeline import build
class CareerPipelineTests(unittest.TestCase):
    def test_never_exports_cv(self):
        profile={"id":"monica","competencies":["npi","manufatura"],"full_cv":"MY PRIVATE PHONE 12345"}
        jobs=[{"title":"NPI Project Manager","company":"Test","description":"NPI manufacturing","location":"Campinas","url":"https://example.com/1"}]
        rows=build(profile,jobs)
        self.assertEqual(len(rows),1)
        self.assertNotIn("MY PRIVATE PHONE",str(rows))
        self.assertEqual(rows[0]["application_status"],"unverified")
    def test_dedup_and_filter(self):
        p={"competencies":["npi"]}
        jobs=[{"title":"Project Manager NPI","location":"Campinas","url":"https://x.test/1"}]*2 + [{"title":"Production Manager","url":"https://x.test/2"}]
        self.assertEqual(len(build(p,jobs)),1)
    def test_requires_profile(self):
        with self.assertRaises(ValueError): build({},[])
if __name__ == "__main__": unittest.main()
