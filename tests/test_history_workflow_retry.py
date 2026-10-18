import unittest
from pathlib import Path

class HistoryWorkflowRetryTests(unittest.TestCase):
    def test_persistence_retries_on_concurrent_push(self):
        workflow = Path(".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn("for attempt in 1 2 3 4 5; do", workflow)
        self.assertIn("git fetch origin main", workflow)
        self.assertIn("git reset --hard origin/main", workflow)
        self.assertIn("merged = dict(latest)", workflow)
        self.assertIn("git push origin HEAD:main", workflow)
        self.assertIn("Could not persist history after 5 synchronization attempts", workflow)
