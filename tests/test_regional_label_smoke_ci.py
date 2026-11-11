import unittest
from pathlib import Path
class RegionalLabelSmoke(unittest.TestCase):
 def test_copy(self):
  self.assertIn('Empresas com vagas coletadas:',Path('src/unified_jobs_dashboard.py').read_text())
