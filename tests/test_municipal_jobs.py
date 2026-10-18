"""Contract tests for municipal sources; never claim unpublished vacancies."""
import unittest
from src.municipal_jobs import collect_source, inject_dashboard

SOURCE = {"name": "PAT Sumaré", "city": "Sumaré", "url": "https://sumare.atende.net/cidadao/pagina/vagas-pat-disponiveis/"}

class MunicipalSourcesTests(unittest.TestCase):
    def test_portal_without_individual_links_is_browse_only(self):
        result = collect_source(SOURCE, lambda url: '<a href="/cidadao">Serviços</a><p>Vagas disponíveis</p>')
        self.assertEqual(result["status"], "browse_only")
        self.assertEqual(result["jobs"], [])

    def test_extract_only_explicit_same_domain_job_links(self):
        html = ('<a href="/vagas/123">Coordenador de Produção</a>'
                '<a href="https://outside.example/vagas/321">Gerente de Manufatura</a>'
                '<a href="/noticias/55">Supervisor de Produção</a>'
                '<a href="/vagas/123">Coordenador de Produção</a>')
        result = collect_source(SOURCE, lambda url: html)
        self.assertEqual(len(result["jobs"]), 1)
        self.assertEqual(result["jobs"][0]["published"], None)
        self.assertFalse(result["jobs"][0]["location_verified"])

    def test_inject_portal_access_without_fabricating_jobs(self):
        report = {"sources": [{**SOURCE, "jobs": [], "status": "browse_only"}], "jobs": []}
        html = inject_dashboard('<main><div id="mainPanelRegional" class="primary-panel"><h1>Regional</h1></div></main>', report)
        self.assertIn('id="municipal-jobs"', html)
        self.assertIn("Consultar vagas no portal oficial", html)
        self.assertNotIn("Verificar anúncio original", html)

    def test_failure_does_not_become_empty_vacancy_claim(self):
        def fail(url):
            raise TimeoutError()
        result = collect_source(SOURCE, fail)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["reason"], "TimeoutError")


    def test_premium_static_body_supported(self):
        from src.unified_jobs_dashboard import render
        report = {"sources": [{**SOURCE, "jobs": [], "status": "browse_only"}], "jobs": []}
        premium = render({"jobs": []}, [])
        result = inject_dashboard(premium, report)
        self.assertIn('id="municipal-jobs"', result)
        self.assertLess(result.index('id="municipal-jobs"'), result.index("</body>"))
        self.assertEqual(result.count('id="municipal-jobs"'), 1)

    def test_municipal_section_is_inside_regional_panel_only(self):
        report = {"sources": [{**SOURCE, "jobs": [], "status": "browse_only"}], "jobs": []}
        page = ('<div id="mainPanelGeneral" class="primary-panel">General</div>'
                '<div id="mainPanelRegional" class="primary-panel">Regional</div>'
                '<div id="mainPanelAI" class="primary-panel">AI</div>')
        result = inject_dashboard(page, report)
        self.assertLess(result.index('id="mainPanelRegional"'), result.index('id="municipal-jobs"'))
        self.assertLess(result.index('id="municipal-jobs"'), result.index('id="mainPanelAI"'))
        self.assertNotIn('id="municipal-jobs"', result.split('id="mainPanelRegional"')[0])

    def test_missing_regional_panel_is_rejected(self):
        report = {"sources": [{**SOURCE, "jobs": [], "status": "browse_only"}], "jobs": []}
        with self.assertRaisesRegex(ValueError, "missing Regional"):
            inject_dashboard('<body><div id="mainPanelGeneral">General</div></body>', report)

    def test_no_duplicate_municipal_section(self):
        report = {"sources": [{**SOURCE, "jobs": [], "status": "browse_only"}], "jobs": []}
        once = inject_dashboard('<body><div id="mainPanelRegional" class="primary-panel"><p>Regional</p></div></body>', report)
        with self.assertRaisesRegex(ValueError, "already present"):
            inject_dashboard(once, report)

if __name__ == "__main__":
    unittest.main()
