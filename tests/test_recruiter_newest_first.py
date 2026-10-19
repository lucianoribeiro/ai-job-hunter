import unittest
from src.unified_jobs_dashboard import render

class RecruiterNewestFirstTests(unittest.TestCase):
    def test_recent_posts_appear_first_across_areas(self):
        monitor={"items":[
          {"title":"Older manufacturing manager","area":"Manufatura","published_at":"2026-10-16T12:00:00+00:00","url":"https://www.linkedin.com/posts/older","modality":"Não informada"},
          {"title":"Newer QA Manager hiring","area":"QA","published_at":"2026-10-18T20:00:00+00:00","url":"https://www.linkedin.com/posts/newer","modality":"Não informada"},
          {"title":"Middle production supervisor","area":"Manufatura","published_at":"2026-10-17T12:00:00+00:00","url":"https://www.linkedin.com/posts/middle","modality":"Não informada"},
        ]}
        page=render({"jobs":[]},[],monitor=monitor)
        self.assertLess(page.index("Newer QA Manager hiring"),page.index("Middle production supervisor"))
        self.assertLess(page.index("Middle production supervisor"),page.index("Older manufacturing manager"))
