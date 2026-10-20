import unittest
from src.monica_page import render

class MonicaBulletsTests(unittest.TestCase):
    def test_bullets_from_cv_and_job_evidence(self):
        job={"title":"Project Manager","company":"Example","location":"Campinas, SP",
             "url":"https://example.com/job","score":82,"application_status":"unverified",
             "location_class":"regional",
             "requirement_analysis":{"matched_requirements":[
                 {"requirement":"gestão de projetos"},
                 {"requirement":"cronogramas"}],
                 "requirements_to_confirm":[{"requirement":"projetos de software"}]}}
        page=render({"jobs":[job]})
        self.assertIn("<li>gestão de projetos</li>",page)
        self.assertIn("<li>cronogramas</li>",page)
        self.assertIn("Requisitos a confirmar",page)
    def test_no_fabricated_skills(self):
        job={"title":"Project Manager","company":"Example","location":"Campinas",
             "url":"https://example.com/job","score":70,"application_status":"unverified",
             "location_class":"regional","requirement_analysis":{"matched_requirements":[]}}
        page=render({"jobs":[job]})
        self.assertIn("Competências ainda não comprovadas",page)
if __name__=="__main__": unittest.main()
