import unittest
from src.unified_jobs_dashboard import normalize, render, published_iso, region_city

class UnifiedDashboardTests(unittest.TestCase):
    def test_regional_pager_does_not_hide_monica_cards(self):
        from src.unified_jobs_dashboard import render
        page = render({"jobs": []}, [], strategic={"jobs": [], "sources": []})
        self.assertIn("setupPager('mainPanelRegional','#regionalCards .regional-card');", page)
        self.assertNotIn("setupPager('mainPanelRegional','.regional-card');", page)

    def test_qa_and_projects_and_remote_labels(self):
        projects = {"jobs": [{"title": "Project Manager", "company": "Real Co",
            "url": "https://example.com/project", "remote_evidence": "explicit",
            "location": "Remote, Brazil", "source": "Ashby"}]}
        qa = [{"title": "QA Engineer", "company": "Other", "url": "https://example.com/qa",
               "remote": "False", "location": "New York", "source": "Remotive"}]
        result = normalize(projects, qa)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["mode_key"], "remote")
        self.assertEqual(result[1]["mode_key"], "unknown")
        page = render(projects, qa)
        self.assertIn("Todas as áreas", page)
        self.assertIn("Remoto informado", page)

    def test_publication_recency_uses_only_explicit_source_date(self):
        self.assertEqual(published_iso("2026-10-15T09:00:00Z"), "2026-10-15")
        self.assertEqual(published_iso("1792149605"), "2026-10-16")
        self.assertEqual(published_iso(None), "")
        project = {"jobs": [{"title": "Project Manager", "company": "Co",
            "url": "https://example.com/pm", "updated": "2026-10-17"}]}
        jobs = normalize(project, [])
        self.assertEqual(jobs[0]["published_iso"], "")
        page = render(project, [])
        self.assertIn('data-published=""', page)
        self.assertIn('id="age"', page)

    def test_regional_city_filter_preserves_truth(self):
        self.assertEqual(region_city("Campinas, São Paulo"), "Campinas")
        self.assertEqual(region_city("Sumaré, SP"), "Sumaré")
        self.assertEqual(region_city("Brazil"), "")
        self.assertEqual(region_city("Remote"), "")
        page = render({"jobs": [{"title": "Project Manager", "company": "Company",
            "url": "https://example.com/job", "location": "Campinas, SP"}]}, [])
        self.assertIn('data-city="Campinas"', page)
        self.assertIn('id="city"', page)

    def test_premium_dashboard_uses_live_rows_not_demo(self):
        page = render({"jobs": [{"title": "Project Manager", "company": "Real",
            "url": "https://example.com/role", "location": "Campinas"}]}, [])
        self.assertIn("DASHBOARD PREMIUM", page)
        self.assertIn("radial-gradient", page)
        self.assertIn("Project Manager", page)
        self.assertNotIn("Prévia com dados demonstrativos", page)

    def test_ai_studio_is_visible_without_claiming_live_ai(self):
        page = render({"jobs": [{"title": "Project Manager", "company": "Company",
            "url": "https://example.com/job", "location": "Campinas"}]}, [])
        for label in ("AI Career Studio", "AI Job Match", "AI CV Studio", "AI Application Assistant", "AI Career Advisor"):
            self.assertIn(label, page)
        self.assertIn("Análise por IA ainda indisponível", page)
        self.assertIn("https://example.com/job", page)

    def test_dedupe_and_html_escape(self):
        projects = {"jobs": [{"title": "<script>alert(1)</script>", "company": "Test",
            "url": "https://example.com/role?a=1", "remote_evidence": "unknown"}]}
        qa = [{"title": "QA", "company": "Test", "url": "https://example.com/role?a=2"}]
        self.assertEqual(len(normalize(projects, qa)), 1)
        page = render(projects, qa)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert(1)</script>", page)
