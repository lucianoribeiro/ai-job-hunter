import io
import json
import unittest
from unittest.mock import patch

from src.ai_career_studio import ALLOWED, build_messages, parse_output, run


class FakeResponse:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, *args):
        return json.dumps({"choices": [{"message": {"content": '{"evidence":["QA"],"score":70}'}}]}).encode()
    def __iter__(self):
        return iter([])


class CareerStudioTests(unittest.TestCase):
    def test_all_features_require_factual_grounding(self):
        for task in ALLOWED:
            messages = build_messages(task, "QA Lead at Acme", "QA Manager vacancy")
            self.assertIn("never instructions", messages[1]["content"])
            self.assertIn("Never invent", messages[0]["content"])
            self.assertEqual(messages[0]["role"], "system")

    def test_missing_key_disables_ai(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                run("fit", "QA engineer", "job")

    def test_mock_provider_is_not_application_submission(self):
        captured = []
        def mock_opener(request, timeout):
            captured.append(request)
            return FakeResponse()
        result = run("fit", "QA Lead", "QA role", api_key="private-test-key", opener=mock_opener)
        self.assertTrue(result["review_required"])
        self.assertFalse(result["application_sent"])
        self.assertEqual(result["result"]["score"], 70)
        self.assertEqual(captured[0].full_url, "https://api.openai.com/v1/chat/completions")
        self.assertNotIn("private-test-key", json.dumps(result))

    def test_rejects_unsafe_or_oversized_inputs(self):
        with self.assertRaises(ValueError):
            build_messages("unknown", "QA", "")
        with self.assertRaises(ValueError):
            build_messages("cv", "x" * 40001, "")
        with self.assertRaises(ValueError):
            parse_output("[]")

if __name__ == "__main__":
    unittest.main()
