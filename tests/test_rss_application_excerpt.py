import unittest
from email.utils import format_datetime
from datetime import datetime, timezone
from src.recruiter_monitor import parse_feed, enrich_application
from unittest.mock import patch

class IndexedApplicationLinksTests(unittest.TestCase):
 def test_rss_excerpt_carries_application_link(self):
  date=format_datetime(datetime(2026,10,18,tzinfo=timezone.utc))
  xml='<rss><channel><item><title>Supervisor de produção - LinkedIn</title><description>Candidate-se: https://lnkd.in/dQqpMZRj</description><link>https://www.linkedin.com/posts/example</link><pubDate>'+date+'</pubDate></item></channel></rss>'
  results=parse_feed(xml,'2026-10-18',max_age_days=30)
  self.assertEqual(len(results),1)
  self.assertIn('lnkd.in/dQqpMZRj',results[0]['indexed_excerpt'])
 def test_enrichment_leaves_unavailable_information_unconfirmed(self):
  record={'title':'Supervisor de produção','indexed_excerpt':'sem link','contract_type':'Não informado'}
  self.assertEqual(enrich_application(record),record)
