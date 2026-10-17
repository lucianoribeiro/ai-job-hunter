import unittest
from src.unified_jobs_dashboard import render

class LocalMatchTests(unittest.TestCase):
    def test_local_profile_workflow_with_real_job(self):
        page=render({"jobs":[{"title":"Gerente de Projetos","company":"Empresa Real","location":"Campinas","url":"https://example.org/real-job"}]},[])
        for id in ("matchFile","matchProfile","matchDescription","matchAnalyze","matchResult","matchFileStatus"):
            self.assertIn('id="'+id+'"',page)
        self.assertIn("https://example.org/real-job",page)
        self.assertIn("matchScore(profile,description,opt)",page)
        self.assertIn("Nenhum texto extraído",page)
        self.assertIn("Cole a descrição/requisitos da vaga",page)
        self.assertIn("Match preliminar:",page)
        self.assertNotIn("sk-test-",page)

    def test_source_vacancy_count_not_modified(self):
        page=render({"jobs":[{"title":"Gerente de Projetos","company":"Acme","location":"Campinas","url":"https://example.org/1"}]},[])
        self.assertIn("Total de vagas<strong>1</strong>",page)
        self.assertIn('id="aiJob"',page)

    def test_compact_upload_ui_status_and_optional_details(self):
        page=render({'jobs': []}, [])
        self.assertIn('id="matchReviewDetails"',page)
        self.assertIn('id="matchDescriptionDetails"',page)
        self.assertIn('Arquivo carregado:',page)
        self.assertIn('Iniciando leitura...',page)
        self.assertIn('matchDescriptionDetails',page)
