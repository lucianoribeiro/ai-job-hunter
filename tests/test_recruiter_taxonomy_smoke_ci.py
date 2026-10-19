import unittest
from src.recruiter_monitor import classify
class RecruiterTaxonomySmoke(unittest.TestCase):
 def test_qa(self):
  self.assertEqual(classify('Head of QA hiring')['area'],'QA')
