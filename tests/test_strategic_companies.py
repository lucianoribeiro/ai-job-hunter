import unittest
from src.strategic_companies import extract_jobs, collect
from src.dashboard import render

class StrategicWatchTests(unittest.TestCase):
    def test_extract_official_job_links_and_ignore_external(self):
        html = '<a href="/jobs/12663551">Analista de Projetos Sumaré</a><a href="https://evil.test/jobs/999999">Fake</a>'
        jobs = extract_jobs(html, "https://honda.gupy.io/", "Honda Brasil")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["url"], "https://honda.gupy.io/jobs/12663551")
        self.assertTrue(jobs[0]["regional"])
        self.assertTrue(jobs[0]["target_role"])

    def test_dynamic_pages_marked_incomplete_not_empty(self):
        data = collect({"companies": [{"name": "Honda Brasil", "url": "https://honda.gupy.io/"}]},
                       fetcher=lambda url: "<html>Javascript required</html>")
        self.assertEqual(data["sources"][0]["state"], "needs_connector")
        self.assertEqual(data["jobs"], [])

    def test_error_is_not_no_vacancies(self):
        def fail(url):
            raise OSError("down")
        data = collect({"companies": [{"name": "Honda Brasil", "url": "https://honda.gupy.io/"}]}, fetcher=fail)
        self.assertEqual(data["sources"][0]["state"], "error")

    def test_dashboard_escapes_untrusted_listing(self):
        output = render({}, strategic={"sources": [], "jobs": [{"title": "<script>x</script>", "company": "Honda", "url": "https://honda.gupy.io/jobs/123456"}]})
        self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("<script>x</script>", output)
        self.assertIn("Empresas estratégicas", output)

if __name__ == "__main__":
    unittest.main()
