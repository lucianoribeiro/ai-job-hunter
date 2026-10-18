import unittest
from src.recruiter_monitor import LINKEDIN_EXTRA_SEARCHES
class LinkedInCI(unittest.TestCase):
 def test_linkedin_queries(self):
  self.assertTrue(all('site:linkedin.com/posts/' in q for q in LINKEDIN_EXTRA_SEARCHES))
