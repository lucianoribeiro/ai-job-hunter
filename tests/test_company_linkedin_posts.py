import unittest
from src.recruiter_monitor import post_origin, COMPANY_POST_SEARCHES
from src.unified_jobs_dashboard import render

class CompanyPostsTests(unittest.TestCase):
 def test_company_author_evidence(self):
  self.assertEqual(post_origin('https://www.linkedin.com/company/acme/posts/'), 'Empresa')
  self.assertEqual(post_origin('https://www.linkedin.com/posts/person-123'), 'Não verificada')
  self.assertEqual(post_origin('https://news.google.com/rss/a','https://linkedin.com/company/acme/'), 'Empresa')
  self.assertEqual(post_origin('https://news.google.com/rss/a','https://linkedin.com/'), 'Não verificada')
 def test_queries_are_linkedin_only(self):
  self.assertGreaterEqual(len(COMPANY_POST_SEARCHES),5)
  self.assertTrue(all('site:linkedin.com/' in q for q in COMPANY_POST_SEARCHES))
 def test_origin_filter_ui(self):
  page=render({'jobs': []}, [])
  self.assertNotIn('id="recruiter-origin"',page)
  self.assertIn('id="recruiter-clear"',page)
  self.assertIn('data-origin=',page)
