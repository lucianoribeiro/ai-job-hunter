import unittest
from datetime import date

from src.linkedin_backfill import backfill, market_scope, month_windows, parse_month


class LinkedInBackfillTests(unittest.TestCase):
    def test_market_scope_requires_explicit_evidence(self):
        self.assertEqual(market_scope("Vaga QA CLT em São Paulo/SP"), "Brasil")
        self.assertEqual(market_scope("QA opportunity in Portugal"), "Internacional")
        self.assertEqual(market_scope("Remote QA opportunity"), "Não identificado")
    def test_month_windows_cover_exact_requested_period(self):
        windows = month_windows(date(2026, 10, 18), 24)
        self.assertEqual(windows[0][0].isoformat(), "2024-11-01")
        self.assertEqual(windows[-1][0].isoformat(), "2026-10-01")
        self.assertEqual(windows[-1][1].isoformat(), "2026-11-01")

    def test_month_parser_filters_area_and_date(self):
        xml = """<rss><channel>
        <item><title>QA Manager hiring - LinkedIn</title><link>https://example.test/qa</link><pubDate>Sun, 18 Oct 2026 10:00:00 GMT</pubDate></item>
        <item><title>Production Manager hiring - LinkedIn</title><link>https://example.test/mfg</link><pubDate>Sun, 18 Oct 2026 10:00:00 GMT</pubDate></item>
        </channel></rss>"""
        rows = parse_month(xml, "QA", date(2026, 10, 1), date(2026, 11, 1))
        self.assertEqual([row["url"] for row in rows], ["https://example.test/qa"])

    def test_failed_month_is_not_recorded_as_zero(self):
        def fetcher(area, start, end):
            if area == "QA":
                return []
            raise OSError("unavailable")
        result = backfill({}, date(2026, 10, 18), months=1, fetcher=fetcher)
        self.assertEqual(result["_coverage"]["2026-10"]["QA"], "ok")
        self.assertEqual(result["_coverage"]["2026-10"]["Manufatura"], "error:OSError")


if __name__ == "__main__":
    unittest.main()
