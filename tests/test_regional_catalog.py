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

    def test_location_unknown_and_city_filter_explanation(self):
        from src.strategic_companies import inferred_city
        self.assertEqual(inferred_city("Analista de Rede Sumaré - SP"), "Sumaré")
        self.assertEqual(inferred_city("Gerente de Projetos Americana - SP"), "Americana")
        self.assertEqual(inferred_city("Analista Financeiro São Paulo - SP"), "")
        report = {"sources": [{"company": "Honda Brasil", "city": "Sumaré", "state": "ok"}],
                  "jobs": [{"title": "Gerente de Projetos Americana - SP",
                            "company": "Honda Brasil", "url": "https://honda.gupy.io/jobs/123",
                            "location": "Americana", "source": "Portal oficial"}]}
        page = render({"jobs": []}, [], strategic=report)
        self.assertIn('data-city="Americana"', page)
        self.assertIn('value="unverified"', page)
        self.assertIn('coleta é parcial', page)

    def test_only_collected_companies_in_filter(self):
        from html import unescape
        report = {"jobs": [{"title": "Analista de Projetos Sumaré", "company": "Honda Brasil",
                             "url": "https://honda.gupy.io/jobs/888", "location": "Sumaré"}],
                  "sources": [{"company": "Honda Brasil", "city": "Sumaré", "state": "ok"},
                              {"company": "PPG", "city": "Sumaré", "state": "manual"}]}
        page = render({"jobs": []}, [], strategic=report)
        options = page.split('id="regionalCompany"', 1)[1].split('</select>', 1)[0]
        self.assertIn('<option value="Honda Brasil">', options)
        self.assertNotIn('<option value="PPG">', options)
        self.assertIn("PPG", page)
        self.assertIn("Vagas coletadas: 1", page)
        self.assertIn("Sumaré (1)", page)
