import unittest
from pathlib import Path
class PersistSmoke(unittest.TestCase):
 def test_retry_present(self):
  self.assertIn('git fetch origin main',Path('.github/workflows/pages.yml').read_text())
