import unittest
import json
from pathlib import Path
from unittest.mock import patch
from src.unified_jobs_dashboard import render

class RecruiterNewestFirstTests(unittest.TestCase):
    def test_recent_posts_appear_first_across_areas(self):
        monitor={"items":[
          {"title":"Older industrial project manager","area":"Manufatura","published_at":"2026-10-16T12:00:00+00:00","url":"https://www.linkedin.com/posts/older","modality":"Não informada"},
          {"title":"Newer QA Manager hiring","area":"QA","published_at":"2026-10-18T20:00:00+00:00","url":"https://www.linkedin.com/posts/newer","modality":"Não informada"},
          {"title":"Middle industrial project coordinator","area":"Manufatura","published_at":"2026-10-17T12:00:00+00:00","url":"https://www.linkedin.com/posts/middle","modality":"Não informada"},
        ]}
        original_exists = Path.exists
        original_read = Path.read_text
        def exists(path):
            return True if str(path) == "data/recruiter_monitor.json" else original_exists(path)
        def read_text(path, *args, **kwargs):
            return json.dumps(monitor) if str(path) == "data/recruiter_monitor.json" else original_read(path, *args, **kwargs)
        with patch.object(Path, "exists", exists), patch.object(Path, "read_text", read_text):
            page=render({"jobs":[]},[])
        self.assertLess(page.index("Newer QA Manager hiring"),page.index("Middle industrial project coordinator"))
        self.assertLess(page.index("Middle industrial project coordinator"),page.index("Older industrial project manager"))
