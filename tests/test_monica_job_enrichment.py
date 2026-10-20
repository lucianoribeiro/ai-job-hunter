import unittest
from src.monica_job_enrichment import enrich
class EnrichmentTests(unittest.TestCase):
    URL="https://jobs.lever.co/example/123"
    def test_city_from_jsonld(self):
        page='<script type="application/ld+json">{"@type":"JobPosting","jobLocation":{"address":{"addressLocality":"Campinas","addressRegion":"SP","addressCountry":"BR"}}}</script>'
        j=enrich({"url":self.URL,"location":"Unknown"},lambda _:page)
        self.assertIn("Campinas",j["location"]);self.assertEqual(j["location_evidence"],"JobPosting.jobLocation")
    def test_remote_brazil(self):
        page='<script type="application/ld+json">{"@type":"JobPosting","jobLocationType":"TELECOMMUTE","applicantLocationRequirements":{"name":"Brazil"}}</script>'
        self.assertEqual(enrich({"url":self.URL,"location":""},lambda _:page)["location"],"Remote, Brazil")
    def test_never_guess_from_employer_address(self):
        page='<script type="application/ld+json">{"@type":"Organization","address":{"addressLocality":"Campinas"}}</script>'
        self.assertEqual(enrich({"url":self.URL,"location":"Unknown"},lambda _:page)["location"],"Unknown")
    def test_disallowed_skipped(self):
        self.assertEqual(enrich({"url":"https://linkedin.com/jobs/1","location":"?"})["location_evidence"],"unknown")
if __name__=="__main__":unittest.main()
