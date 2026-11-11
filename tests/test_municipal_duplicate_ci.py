import unittest
from src.municipal_jobs import inject_dashboard

class DuplicateMunicipalSmoke(unittest.TestCase):
    def test_repeat_injection_is_rejected(self):
        report = {'sources': [], 'jobs': []}
        page = '<div id="mainPanelRegional"></div>'
        once = inject_dashboard(page, report)
        with self.assertRaisesRegex(ValueError, 'already present'):
            inject_dashboard(once, report)
