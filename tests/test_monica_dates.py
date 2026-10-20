import unittest
from src.monica_dates import publication_date, display_date
from src.monica_page import render
class MonicaDatesTests(unittest.TestCase):
    def test_iso_and_brazil_format(self):
        self.assertEqual(display_date("2026-10-15T12:00:00Z"),"15/10/2026")
        self.assertIsNone(publication_date("há 2 dias"))
        self.assertEqual(display_date(""),"Data não informada")
    def test_newest_first_unknown_last(self):
        base={"title":"Project Manager","location":"Campinas, SP","score":80,
              "company":"Test","application_status":"unverified","location_class":"regional"}
        items=[{**base,"url":"https://example.com/1","published_at":"2026-10-10"},
               {**base,"url":"https://example.com/2","published_at":""},
               {**base,"url":"https://example.com/3","published_at":"2026-10-18"}]
        html=render({"jobs":items})
        self.assertLess(html.index("18/10/2026"),html.index("10/10/2026"))
        self.assertLess(html.index("10/10/2026"),html.index("Data não informada"))
if __name__=="__main__":unittest.main()
