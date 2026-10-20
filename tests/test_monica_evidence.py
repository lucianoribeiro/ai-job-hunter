import unittest
from src.monica_evidence import explain
class EvidenceTests(unittest.TestCase):
    def test_cv_evidence_and_gap(self):
        job={"description":"NPI project management, Power BI and Scrum"}
        profile={"competencies":["npi","gestao de projetos"],"private":"PRIVATE CV PHONE 123"}
        report=explain(job,profile)
        self.assertTrue(any(x["requirement"]=="npi" for x in report["matched_requirements"]))
        self.assertTrue(any(x["requirement"]=="power bi" for x in report["requirements_to_confirm"]))
        self.assertNotIn("PRIVATE CV PHONE",str(report))
    def test_no_description_is_uncertain(self):
        self.assertFalse(explain({},{"competencies":["npi"]})["source_has_description"])
if __name__=="__main__":unittest.main()
