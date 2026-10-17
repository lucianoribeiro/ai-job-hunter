import unittest
from src.unified_jobs_dashboard import render

class PagesVisibilityTests(unittest.TestCase):
    def test_main_tabs_keep_studio_and_regional_catalog(self):
        page = render({"jobs": []}, [], strategic={"sources": [{"company": "Honda Brasil", "state": "needs_connector"}], "jobs": []})
        self.assertIn("AI Career Studio", page)
        self.assertIn("Vagas regionais", page)
        self.assertIn('id="mainPanelGeneral" class="primary-panel"', page)
        self.assertIn('id="mainPanelRegional" class="primary-panel"', page)
        self.assertIn('id="mainPanelAI" class="primary-panel"', page)
        self.assertIn('id="mainTabGeneral"', page)
        self.assertIn('id="mainTabRegional"', page)
        self.assertIn('id="mainTabAI"', page)
        self.assertIn('role="tablist"', page)
        self.assertIn("activateMainTab(0)", page)
        self.assertLess(page.index('id="mainPanelGeneral"'), page.index('id="mainPanelRegional"'))
        self.assertLess(page.index('id="mainPanelRegional"'), page.index('id="mainPanelAI"'))
        self.assertIn("ArrowRight", page)
        self.assertIn("ArrowLeft", page)
        self.assertIn("needs_connector", page)

    def test_unsafe_honda_title_is_escaped(self):
        page = render({"jobs": []}, [], strategic={"jobs": [{"title": "<img src=x onerror=alert(1)>", "url": "https://honda.gupy.io/jobs/123456", "company": "Honda"}]})
        self.assertIn("&lt;img", page)
        self.assertNotIn("<img src=x onerror=alert(1)>", page)

    def test_ai_job_selector_contains_real_jobs_not_template_code(self):
        page = render({"jobs": [{"title": "Gerente de Projetos", "company": "Acme",
                                 "location": "Campinas", "url": "https://example.com/jobs/123"}]}, [])
        selection = page.split('id="aiJob"', 1)[1].split("</select>", 1)[0]
        self.assertIn("Gerente de Projetos · Acme", selection)
        self.assertIn('value="https://example.com/jobs/123"', selection)
        self.assertNotIn('j["title"]', selection)
        self.assertNotIn('__AI_JOB_OPTIONS__', selection)
        self.assertIn('Selecionar uma vaga do catálogo...', selection)

    def test_main_tabs_and_both_paginators(self):
        jobs=[{"title":f"Gerente de Projetos {i}","company":"Acme","location":"Americana, SP",
               "url":f"https://example.com/job/{i}"} for i in range(15)]
        page=render({"jobs":jobs},[],strategic={"jobs":[],"sources":[]})
        self.assertEqual(page.count('class="page-controls"'),2)
        self.assertIn('option value="10"',page)
        self.assertIn('option value="all"',page)
        self.assertIn("setupPager('mainPanelGeneral','tbody tr')",page)
        self.assertIn("setupPager('mainPanelRegional','.regional-card')",page)
        self.assertIn("selectTab(0,false)",page)
        self.assertIn("panel.style.display=active?'':'none'",page)
        self.assertEqual(page.count('data-area="Projetos"'),15)
