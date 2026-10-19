import unittest
from src.recruiter_monitor import classify, QA_LEADERSHIP_SEARCHES, MANUFACTURING_SEARCHES

class RecruiterSearchTaxonomyTests(unittest.TestCase):
    def test_qa_leadership_classification(self):
        for title in ("Head of QA hiring", "Quality Engineering Lead vacancy", "Software Test Manager remote", "Líder de Testes contratando", "QA Tech Lead hiring", "SDET Lead vacancy"):
            with self.subTest(title=title):
                self.assertEqual(classify(title)["area"], "QA")
    def test_manufacturing_management_classification(self):
        for title in ("Manufacturing Coordinator hiring", "Gerente de fábrica vaga", "Factory Manager opportunity", "Coordenador industrial oportunidade"):
            with self.subTest(title=title):
                self.assertEqual(classify(title)["area"], "Manufatura")
    def test_industrial_quality_does_not_become_software_qa(self):
        self.assertNotEqual(classify("Quality Control Manager manufacturing")["area"], "QA")
        self.assertEqual(classify("QA Engineer software testing")["area"], "QA")
    def test_linkedin_public_queries(self):
        self.assertGreaterEqual(len(QA_LEADERSHIP_SEARCHES), 8)
        self.assertTrue(all("site:linkedin.com/posts/" in x for x in QA_LEADERSHIP_SEARCHES))
        self.assertIn('site:linkedin.com/posts/ "gerente de fábrica" contratação', MANUFACTURING_SEARCHES)
