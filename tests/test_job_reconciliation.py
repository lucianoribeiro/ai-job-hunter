import unittest
from src.unified_jobs_dashboard import render

class JobReconciliationTests(unittest.TestCase):
    def test_all_source_jobs_are_reconciled(self):
        data={"sources":[{"company":"Honda Brasil","city":"Sumaré","state":"ok"}],
          "jobs":[
             {"company":"Honda Brasil","title":"Analista Sumaré","location":"Sumaré","url":"https://honda.gupy.io/jobs/100"},
             {"company":"Honda Brasil","title":"Analista Manaus","location":"Não informado","url":"https://honda.gupy.io/jobs/200"},
             {"company":"Honda Brasil","title":"Analista sem URL","location":"Sumaré","url":""},
             {"company":"Honda Brasil","title":"Analista Sumaré","location":"Sumaré","url":"https://honda.gupy.io/jobs/100"}]}
        page=render({"jobs":[]},[],strategic=data)
        self.assertIn("Retornados pelo coletor de empresas: 4",page)
        self.assertIn("Exibidos: 1",page)
        self.assertIn("Duplicados: 1",page)
        self.assertIn("Localidade fora da região: 1",page)
        self.assertIn("Registros inválidos: 1",page)
        self.assertEqual(page.count('class="regional-card"'),1)
