import unittest
from src.ci_recovery import diagnose
class RecoveryTests(unittest.TestCase):
    def test_obsolete_test_not_auto_removed(self):
        self.assertEqual(diagnose('manufacturingLeadershipAlert IndexError: list index out of range')['action'],'human_review')
    def test_transient_retry(self):
        self.assertEqual(diagnose('503 Service Unavailable')['action'],'retry_once')
    def test_code_failure_no_retry(self):
        self.assertEqual(diagnose('FAILED (errors=1)')['action'],'human_review')
    def test_unknown_no_retry(self):
        self.assertEqual(diagnose('problem')['action'],'human_review')
if __name__=="__main__":unittest.main()
