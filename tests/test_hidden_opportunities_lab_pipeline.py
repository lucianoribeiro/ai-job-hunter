import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.hidden_opportunities_lab import investigate, update_history
from src.hidden_opportunities_lab_source import discover


class HiddenLabPipelineTests(unittest.TestCase):
    def test_history_tracks_new_and_repeated(self):
        records = [{"url": "https://www.linkedin.com/posts/qa-team",
                    "excerpt": "We are hiring quality engineering leadership"}]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "history.json"
            first = update_history(investigate(records), path)
            self.assertEqual(first["new_signals_this_run"], 1)
            self.assertEqual(first["repeated_signals_this_run"], 0)
            second = update_history(investigate(records), path)
            self.assertEqual(second["new_signals_this_run"], 0)
            self.assertEqual(second["repeated_signals_this_run"], 1)
            self.assertEqual(second["confirmed_hidden_vacancies"], 0)

    def test_source_unavailable_fails_open_only_to_diagnostics(self):
        with patch("src.hidden_opportunities_lab_source.shutil.which", return_value=None):
            result = discover()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["records"], [])
        self.assertTrue(result["errors"])

    def test_structured_source_preserves_own_url(self):
        payload = '{"results":[{"title":"Hiring a Quality Engineering Lead","url":"https://www.linkedin.com/posts/team-qa","snippet":"We are hiring QA leadership."}]}'
        class Response:
            returncode = 0
            stdout = payload
            stderr = ""
        with patch("src.hidden_opportunities_lab_source.shutil.which", return_value="/tmp/agent-reach"):
            with patch("src.hidden_opportunities_lab_source.subprocess.run", return_value=Response()):
                result = discover()
        self.assertEqual(result["status"], "complete")
        self.assertGreaterEqual(len(result["records"]), 1)
        self.assertEqual(result["records"][0]["url"], "https://www.linkedin.com/posts/team-qa")


if __name__ == "__main__":
    unittest.main()
