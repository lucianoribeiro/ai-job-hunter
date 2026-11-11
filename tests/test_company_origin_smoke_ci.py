import unittest
from src.recruiter_monitor import post_origin
class CompanyOriginSmoke(unittest.TestCase):
 def test_url(self):
  self.assertEqual(post_origin('https://www.linkedin.com/company/example/posts/'),'Empresa')
