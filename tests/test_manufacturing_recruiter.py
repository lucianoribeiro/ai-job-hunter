import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from src.recruiter_monitor import classify, parse_feed, MANUFACTURING_SEARCHES

class ManufacturingRecruiterTests(unittest.TestCase):
    def test_industrial_leadership_classification(self):
        for title in ("Plant Manager hiring", "Gerente industrial vaga",
                      "Coordenador de produção oportunidade"):
            self.assertEqual(classify(title)["area"], "Manufatura")
        self.assertEqual(classify("SDET - Software QA hiring")["area"], "QA")

    def test_manufacturing_seven_day_window_without_changing_qa(self):
        today=datetime(2026, 10, 18, tzinfo=timezone.utc)
        published=format_datetime(today-timedelta(days=3))
        xml=f"<rss><channel><item><title>Coordenador de produção - vaga</title><link>https://www.linkedin.com/posts/test-123</link><pubDate>{published}</pubDate></item></channel></rss>"
        self.assertEqual(len(parse_feed(xml, "2026-10-18", max_age_days=7, manufacturing_only=True)),1)
        self.assertEqual(len(parse_feed(xml, "2026-10-18")),0)

    def test_nonleadership_post_filtered_in_manufacturing_feed(self):
        published=format_datetime(datetime(2026,10,18,tzinfo=timezone.utc))
        xml=f"<rss><channel><item><title>Production engineer QA hiring</title><link>https://www.linkedin.com/posts/test-456</link><pubDate>{published}</pubDate></item></channel></rss>"
        self.assertEqual(parse_feed(xml,"2026-10-18",max_age_days=7,manufacturing_only=True),[])
        self.assertGreaterEqual(len(MANUFACTURING_SEARCHES),10)

    def test_qa_30_day_window(self):
        from datetime import datetime, timezone, timedelta
        from email.utils import format_datetime
        day=datetime(2026, 10, 18, tzinfo=timezone.utc)
        published=format_datetime(day-timedelta(days=29))
        xml=f'<rss><channel><item><title>Hiring Senior QA Engineer</title><link>https://www.linkedin.com/posts/test-qa</link><pubDate>{published}</pubDate></item></channel></rss>'
        self.assertEqual(len(parse_feed(xml, '2026-10-18', max_age_days=30)), 1)
        self.assertEqual(len(parse_feed(xml, '2026-10-18', max_age_days=7)), 0)

    def test_linkedin_only_and_job_intent(self):
        published=format_datetime(datetime(2026,10,18,tzinfo=timezone.utc))
        def feed(url, title):
            return '<rss><channel><item><title>'+title+'</title><link>'+url+'</link><pubDate>'+published+'</pubDate></item></channel></rss>'
        self.assertEqual(parse_feed(feed('https://other.example/posts/1','Hiring QA Engineer'), '2026-10-18',max_age_days=30), [])
        self.assertEqual(parse_feed(feed('https://www.linkedin.com/posts/a','QA interview tips'), '2026-10-18',max_age_days=30), [])
        self.assertEqual(len(parse_feed(feed('https://www.linkedin.com/posts/b','Hiring QA Engineer'), '2026-10-18',max_age_days=30)),1)
