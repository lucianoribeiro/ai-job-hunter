import json
import unittest
from pathlib import Path
from src.strategic_companies import collect
from src.unified_jobs_dashboard import render

class ThreeCitiesTests(unittest.TestCase):
    def test_scope_and_directory(self):
        config=json.loads(Path("config/strategic_companies.json").read_text(encoding="utf-8"))
        self.assertEqual(set(config["cities"]), {"Sumaré", "Paulínia", "Americana"})
        self.assertEqual({c["city"] for c in config["companies"]}, set(config["cities"]))
        report=collect(config, fetcher=lambda _: "<html></html>")
        self.assertEqual(len(report["sources"]), len(config["companies"]))
        page=render({"jobs":[]}, [], strategic=report)
        for city in config["cities"]:
            self.assertIn(city, page)
        self.assertIn("Goodyear", page)
        self.assertIn("Honda Brasil", page)

    def test_manual_sources_are_not_reported_as_empty_jobs(self):
        config={"companies":[{"name":"Company", "city":"Americana", "url":"", "monitor":"manual"}]}
        report=collect(config, fetcher=lambda _: (_ for _ in ()).throw(AssertionError("must not fetch")))
        self.assertEqual(report["sources"][0]["state"],"manual")
