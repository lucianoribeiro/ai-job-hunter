import json
import unittest
from pathlib import Path
from src.monica_pipeline import build, collect
class CuratedLinkedInTests(unittest.TestCase):
    def test_imported_set_has_13_distinct_names(self):
        jobs=collect(Path("data/monica_linkedin_jobs.json"))
        self.assertEqual(len(jobs),13)
        self.assertEqual(len(set(j["company"] for j in jobs)),13)
        self.assertEqual(sum(bool(j.get("source_listing_only")) for j in jobs),1)
        self.assertEqual(sum(j.get("application_status")=="closed" for j in jobs),2)
    def test_no_closed_or_listing_only_active(self):
        jobs=collect(Path("data/monica_linkedin_jobs.json"))
        selected=build({"id":"monica","competencies":["gestao de projetos","cronogramas","stakeholders"]},jobs)
        self.assertFalse(any(j["company"] in ("Arcor do Brasil","Círculo","3M") for j in selected))
        self.assertTrue(all(j["application_status"]!="apply_indicated" for j in selected))
if __name__=="__main__":unittest.main()
