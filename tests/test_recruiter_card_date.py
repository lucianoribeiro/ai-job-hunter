import unittest
from src.unified_jobs_dashboard import recruiter_index_date

class RecruiterCardDateTests(unittest.TestCase):
    def test_brazil_timezone_and_accessible_label(self):
        value, accessible = recruiter_index_date("2026-10-18T14:45:27+00:00")
        self.assertEqual(value, "18/10/2026 às 11h45")
        self.assertIn("11 horas e 45 minutos", accessible)

    def test_invalid_index_date_not_invented(self):
        self.assertEqual(recruiter_index_date("unknown"), ("Data do índice não informada", ""))
