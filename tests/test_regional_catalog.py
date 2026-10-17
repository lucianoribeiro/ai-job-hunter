import unittest
from src.unified_jobs_dashboard import render

class RegionalCatalogTests(unittest.TestCase):
    def test_filters_and_inline_vacancy(self):
        report = {"jobs": [{"title": "Gerente de Projetos", "company": "Empresa Exemplo",
                            "location": "Americana, SP", "url": "https://example.org/jobs/1",
                            "source": "Lever", "remote_evidence": "unknown"}]}
        page = render(report, [], strategic={"sources": [{"company": "Honda Brasil", "city": "Sumaré", "state": "manual"}]})
        self.assertIn('id="regionalCompany"', page)
        self.assertIn('id="regionalCity"', page)
        self.assertIn('id="regionalArea"', page)
        self.assertIn("Gerente de Projetos", page)
        self.assertIn("Ver informações da vaga", page)
        self.assertIn("Honda Brasil", page)

    def test_unverified_company_not_a_job(self):
        page = render({"jobs": []}, [], strategic={"sources": [{"company": "Honda Brasil", "city": "Sumaré", "state": "manual"}]})
        self.assertIn("Honda Brasil", page)
        self.assertIn("Nenhum anúncio regional foi obtido", page)
        self.assertNotIn('class="regional-card"', page)
