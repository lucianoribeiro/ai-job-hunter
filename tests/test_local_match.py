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
        self.assertIn("Para calcular um match confiável",page)
        self.assertIn("Match preliminar:",page)
        self.assertNotIn("sk-test-",page)

    def test_source_vacancy_count_not_modified(self):
        page=render({"jobs":[{"title":"Gerente de Projetos","company":"Acme","location":"Campinas","url":"https://example.org/1"}]},[])
        self.assertIn('Total de vagas<strong id="summary-total" aria-live="polite">1</strong>',page)
        self.assertIn('id="aiJob"',page)

    def test_compact_upload_ui_status_and_optional_details(self):
        page=render({'jobs': []}, [])
        self.assertIn('id="matchReviewDetails"',page)
        self.assertIn('id="matchDescriptionDetails"',page)
        self.assertIn('Arquivo carregado:',page)
        self.assertIn('Iniciando leitura...',page)
        self.assertIn('matchDescriptionDetails',page)

    def test_match_is_independent_and_reports_missing_job_or_profile(self):
        page=render({'jobs': []}, [])
        scripts=page.split('<script>')
        self.assertGreaterEqual(len(scripts),4)
        match_script=scripts[-1].split('</script>',1)[0]
        self.assertIn("matchId('matchAnalyze').addEventListener",match_script)
        self.assertIn('Selecione uma vaga real para calcular',match_script)
        self.assertIn('aguarde a confirmação da extração',match_script)
        self.assertIn('Não foi possível iniciar a análise local',match_script)

    def test_rendered_match_script_has_valid_javascript(self):
        import re
        import shutil
        import subprocess
        page=render({'jobs': []}, [])
        scripts=re.findall(r'<script>(.*?)</script>',page,re.S)
        self.assertGreaterEqual(len(scripts),3)
        if shutil.which('node'):
            for code in scripts:
                result=subprocess.run(['node','--check'],input=code,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_clean_three_step_match_flow_keeps_advanced_inputs(self):
        page=render({'jobs': []}, [])
        self.assertIn('1. Selecione uma vaga',page)
        self.assertIn('2. Envie seu currículo',page)
        self.assertIn('3. Analisar compatibilidade',page)
        self.assertIn('id="matchFilters"',page)
        self.assertIn('id="matchReviewDetails"',page)
        self.assertIn('id="matchDescriptionDetails"',page)
        self.assertIn('id="matchAnalyze"',page)
        self.assertIn('id="matchResult"',page)

    def test_source_requirements_prefill_and_missing_description(self):
        report={'jobs':[{'title':'Gerente de Projetos','company':'Empresa',
            'location':'Sumaré','url':'https://example.org/job/42',
            'description':'Gestão de cronogramas, orçamento e liderança de equipes.'}]}
        page=render(report,[])
        self.assertIn('data-description="Gestão de cronogramas, orçamento e liderança de equipes."',page)
        self.assertIn("jobSelect.addEventListener('change',fillJobRequirements)",page)
        self.assertIn('id="matchRequirementsStatus"',page)
        self.assertIn("Esta fonte não disponibilizou a descrição completa",page)
