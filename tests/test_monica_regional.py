import unittest
from src.monica_location import location_category
from src.monica_pipeline import build
PROFILE={"id":"monica","competencies":["npi","gestao de projetos","manufatura"]}
def job(url,location,title="NPI Project Manager"):
    return {"url":url,"title":title,"location":location,"description":"NPI manufacturing project management","company":"Example"}
class MonicaRegionalTests(unittest.TestCase):
    def test_regions(self):
        self.assertEqual(location_category(job("https://x.test/1","Jaguariúna, SP")),"regional")
    def test_foreign_exclusion(self):
        self.assertEqual(location_category(job("https://x.test/1","Ho Chi Minh, Vietnam")),"out_of_scope")
        self.assertEqual(len(build(PROFILE,[job("https://x.test/1","Ho Chi Minh, Vietnam")])),0)
    def test_remote_brazil(self):
        self.assertEqual(location_category(job("https://x.test/1","Remote, Brazil")),"remote_br")
    def test_remote_global_needs_review(self):
        self.assertEqual(location_category(job("https://x.test/1","Remote, Global")),"remote_review")
    def test_closed_not_recommended(self):
        items=build(PROFILE,[job("https://jobs.lever.co/x/1","Campinas")],
                    True,lambda _ :{"status":"closed","reason":"closed"})
        self.assertEqual(items,[])
    def test_unverified_not_open(self):
        items=build(PROFILE,[job("https://x.test/1","Campinas")])
        self.assertEqual(items[0]["application_status"],"unverified")
        self.assertIn(items[0]["tier"],("recommended","review"))
if __name__=="__main__":unittest.main()
