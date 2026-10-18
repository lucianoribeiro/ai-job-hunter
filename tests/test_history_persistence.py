import unittest
from src.job_history import retain as retain_jobs
from src.linkedin_history import retain as retain_posts

class HistoryPersistenceTests(unittest.TestCase):
    def test_job_records_are_deduplicated_and_updated(self):
        rows=[{"url":"https://example.com/jobs/1","title":"QA Engineer","company":"Example","source":"Public"}]
        first=retain_jobs({},rows,"2026-10-18")
        self.assertEqual(len(first),1)
        second=retain_jobs(first,rows,"2026-10-19")
        self.assertEqual(len(second),1)
        record=next(iter(second.values()))
        self.assertEqual(record["first_seen"],"2026-10-18")
        self.assertEqual(record["last_seen"],"2026-10-19")

    def test_linkedin_retains_origin_and_first_seen(self):
        item={"area":"QA","url":"https://linkedin.com/company/example/posts/1","title":"QA hiring","published_at":"2026-10-18T08:00:00+00:00","post_origin":"Empresa"}
        first=retain_posts({},{"date_utc":"2026-10-18","items":[item]})
        second=retain_posts(first,{"date_utc":"2026-10-19","items":[item]})
        self.assertEqual(len(second),1)
        record=next(iter(second.values()))
        self.assertEqual(record["post_origin"],"Empresa")
        self.assertEqual(record["first_seen"],"2026-10-18")
        self.assertEqual(record["last_seen"],"2026-10-19")
