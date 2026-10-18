import unittest
from unittest.mock import patch
from io import BytesIO
import json
from src.strategic_companies import collect, ppg_public_jobs, workday_3m_jobs

class StrategicCompanyIntegrationsTests(unittest.TestCase):
    def test_ppg_official_links_only(self):
        html = '<a href="/br/pt/job/PIIPIIUSJR123/Engenheiro-Qualidade-Sumare">Engenheiro Qualidade Sumaré</a><a href="https://other.example/br/pt/job/x">Gerente Sumaré</a>'
        jobs = ppg_public_jobs(html, 'https://careers.ppg.com/br/pt/search-results', 'PPG')
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['location'], 'Sumaré')

    def test_3m_workday_public_structured_result(self):
        payload = json.dumps({"jobPostings":[{"title":"Project Manager Sumaré","locationsText":"BR, São Paulo, Sumare","externalPath":"/job/Project-Manager_R123"},{"title":"Other","locationsText":"US","externalPath":"/job/Other_R999"}]}).encode("utf-8")
        class Response(BytesIO):
            pass
        with patch('src.strategic_companies.urlopen', return_value=Response(payload)):
            jobs=workday_3m_jobs('3M Brasil')
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]['location'],'Sumaré')
        self.assertIn('/Search/job/',jobs[0]['url'])

    def test_other_manual_companies_remain_manual(self):
        config={'companies':[{'name':'Goodyear','city':'Americana','url':'https://example.com','monitor':'manual'}]}
        self.assertEqual(collect(config)['sources'][0]['state'],'manual')
