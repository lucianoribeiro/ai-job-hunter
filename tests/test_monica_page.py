import unittest
from src.monica_page import eligible,render
class MonicaPageTests(unittest.TestCase):
    def item(self,**kwargs):
        return {"title":"NPI Project Manager","company":"Example","location":"Campinas, SP","url":"https://example.org/jobs/1","score":80,"application_status":"unverified","evidence":["NPI"],"gaps":[]}|kwargs
    def test_regional(self):self.assertTrue(eligible(self.item()))
    def test_exclude_overseas(self):self.assertFalse(eligible(self.item(location="Ho Chi Minh, Vietnam")))
    def test_exclude_low_score(self):self.assertFalse(eligible(self.item(score=10)))
    def test_exclude_closed(self):self.assertFalse(eligible(self.item(application_status="closed")))
    def test_remote_brazil(self):self.assertTrue(eligible(self.item(location="Remote, Brazil")))
    def test_remote_other_country(self):self.assertFalse(eligible(self.item(location="Remote, Vietnam")))
    def test_no_noise(self):
        page=render({"jobs":[self.item(),self.item(location="Tokyo, Japan",url="https://example.org/jobs/2")]})
        self.assertIn("Campinas",page)
        self.assertNotIn("Tokyo",page)
if __name__=="__main__":unittest.main()
