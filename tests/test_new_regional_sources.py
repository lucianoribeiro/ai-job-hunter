import unittest
from src.strategic_companies import inspect_official_portal, inspect_petrobras_concursos, collect

class NewRegionalSourcesTests(unittest.TestCase):
    def test_goodyear_official_links_do_not_create_jobs(self):
        html='<a href="https://jobs.goodyear.com/job/123">Vagas corporativo</a><a href="https://external.example/job/222">Vagas</a>'
        urls=inspect_official_portal(html,"https://www.goodyear.com.br/trabalhe-conosco/","goodyear_careers")
        self.assertEqual(urls,["https://jobs.goodyear.com/job/123"])

    def test_braskem_oracle_career_link(self):
        html='<a href="https://epiw.fa.la1.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1">Veja nossas oportunidades</a>'
        urls=inspect_official_portal(html,"https://www.braskem.com.br/carreira","braskem_careers")
        self.assertEqual(len(urls),1)

    def test_petrobras_closed_registrations(self):
        self.assertTrue(inspect_petrobras_concursos("Não temos inscrições abertas para concursos no momento"))
        self.assertFalse(inspect_petrobras_concursos("Inscrições abertas até 30/10/2026"))

    def test_portal_monitor_not_counted_as_job(self):
        config={"companies":[{"name":"Braskem","city":"Paulínia","url":"https://www.braskem.com.br/carreira","monitor":"public_links","connector":"braskem_careers"}]}
        result=collect(config,fetcher=lambda _: '<a href="https://www.braskem.com.br/carreira">Carreiras</a>')
        self.assertEqual(result["jobs"],[])
        self.assertEqual(result["sources"][0]["state"],"portal_only")
