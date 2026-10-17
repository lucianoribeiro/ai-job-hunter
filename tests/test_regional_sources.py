import unittest
from unittest.mock import patch
from src.public_sources import smartrecruiters, recruitee

class PublicRegionalSourceTests(unittest.TestCase):
    @patch("src.public_sources.get")
    def test_smartrecruiters_location_and_date(self, get):
        get.return_value = {"totalFound": 1, "content": [{"id":"123", "name":"Project Manager", "releasedDate":"2026-10-01", "location":{"city":"Paulínia","region":"SP","country":"BR"}}]}
        jobs = smartrecruiters("Syngenta","SyngentaGroup")
        self.assertEqual(len(jobs), 1)
        self.assertIn("Paulínia", jobs[0]["location"])
        self.assertEqual(jobs[0]["published"], "2026-10-01")
    @patch("src.public_sources.get")
    def test_recruitee(self, get):
        get.return_value = {"offers":[{"id":1,"title":"Gerente de Projetos","slug":"gerente-de-projetos","status":"published","locations":[{"city":"Campinas"}]}]}
        jobs = recruitee("Empresa","empresa")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "Recruitee")

if __name__ == "__main__":
    unittest.main()
