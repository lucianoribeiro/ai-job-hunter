import unittest
from src.himalayas_jobs import collect
from src.unified_jobs_dashboard import normalize


class HimalayasTests(unittest.TestCase):
    def test_joins_real_source_shape_and_rejects_irrelevant_roles(self):
        def getter(url):
            return {"jobs": [
                {"title": "QA Engineer", "companyName": "Example", "url": "https://himalayas.app/jobs/1",
                 "pubDate": "2026-10-15", "locationRestrictions": ["Brazil"]},
                {"title": "Sales Executive", "companyName": "Example", "url": "https://himalayas.app/jobs/2"}]}
        data = collect(getter)
        self.assertEqual(len(data["jobs"]), 1)
        self.assertEqual(data["jobs"][0]["source"], "Himalayas")
        rows = normalize({"jobs": []}, [], remote_jobs=data["jobs"])
        self.assertEqual(rows[0]["published_iso"], "2026-10-15")
        self.assertEqual(rows[0]["area"], "QA")

if __name__ == "__main__":
    unittest.main()
