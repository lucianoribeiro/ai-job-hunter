import unittest
import json
import os
import tempfile
from pathlib import Path
from src.monica_embed import render

class ImportedRegionalJobsTests(unittest.TestCase):
    def test_four_curated_jobs_visible_without_private_cv(self):
        html=render({"jobs":[]})
        for company in ("VRH Consultoria","LGS Engenharia","Stefanini"):
            self.assertIn(company,html)
        self.assertIn("gerente-projetos-iii-jaguariuna-sp",html)
        self.assertIn("gerente-projetos/4321063",html) if False else None
        self.assertIn("coordenador-de-projetos/4321063",html)
        self.assertIn("Candidatura não verificada",html)
        self.assertIn("anúncio previamente identificado",html)
        self.assertIn("Aderência: 88/100",html)
        self.assertIn("Aderência: 84/100",html)
        self.assertIn("Prioridade para Mônica: 2 oportunidades",html)
        self.assertLess(html.index("VRH Consultoria"),html.index("AB InBev") if "AB InBev" in html else len(html))
        self.assertIn("Vaga importada · Região de Nova Odessa",html)
    def test_total_matches_all_rendered_cards(self):
        html=render({"jobs":[]})
        self.assertEqual(html.count('<article class="regional-card"'), 17)
        self.assertIn('id="monica-total-cards">17</strong>', html)
        self.assertIn('Fim da lista · 17 cartões exibidos', html)

    def test_public_discoveries_render_without_private_profile_and_deduplicate(self):
        old_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                Path("data").mkdir()
                job = {"title": "Coordenador de Projetos", "company": "Empresa Teste",
                       "location": "Americana, SP", "source": "Portal oficial",
                       "url": "https://example.com/jobs/123"}
                Path("data/monica_regional_sp.json").write_text(
                    json.dumps({"collected_at": "2026-10-25T18:03:00+00:00", "jobs": [job, job, {**job, "url": "https://example.com/jobs/closed",
                                           "application_status": "closed"}]}), encoding="utf-8")
                html = render({"jobs": []})
                self.assertEqual(html.count('href="https://example.com/jobs/123"'), 1)
                self.assertNotIn("https://example.com/jobs/closed", html)
                self.assertIn("Vaga coletada automaticamente", html)
                self.assertIn("25/10/2026 às 15h03", html)
                self.assertIn('id="monica-last-collection"', html)
                self.assertIn("Aderência: a calcular", html)
                self.assertIn('id="monica-total-cards">1</strong>', html)
        finally:
            os.chdir(old_cwd)

    def test_score_labels_and_priority_message(self):
        html=render({"jobs":[]})
        self.assertIn("Aderência: 88/100",html)
        self.assertIn("Aderência: 84/100",html)
        self.assertIn("Aderência: a calcular",html)
        self.assertIn("Prioridade para Mônica: 2 oportunidades",html)
        self.assertIn("revisão manual",html)

    def test_not_duplicated_when_cv_feed_contains_listing(self):
        job={"url":"https://www.netvagas.com.br/empresa/anuncios/a1724116/gerente-de-projetos/",
             "title":"Gerente de Projetos","company":"VRH Consultoria",
             "location":"Paulínia, SP","score":85,"application_status":"unverified"}
        html=render({"jobs":[job]})
        self.assertEqual(html.count('href="https://www.netvagas.com.br/empresa/anuncios/a1724116/gerente-de-projetos/"'),1)


    def test_mixed_sources_sorted_by_publication_and_missing_dates_last(self):
        old_cwd = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.chdir(tmp)
                Path("data").mkdir()
                Path("data/monica_regional_reviewed.json").write_text(json.dumps({"jobs": [
                    {"title": "Old reviewed", "company": "Old Co", "location": "Campinas, SP",
                     "url": "https://example.com/old", "published_at": "2026-10-10",
                     "preliminary_match_score": 88}
                ]}), encoding="utf-8")
                Path("data/monica_regional_sp.json").write_text(json.dumps({"jobs": [
                    {"title": "Newest discovered", "company": "New Co", "location": "Americana, SP",
                     "url": "https://example.com/new", "published_at": "2026-10-24"},
                    {"title": "Undated", "company": "No Date Co", "location": "Sumaré, SP",
                     "url": "https://example.com/undated"}
                ]}), encoding="utf-8")
                page = render({"jobs": []})
                self.assertLess(page.index("Newest discovered"), page.index("Old reviewed"))
                self.assertLess(page.index("Old reviewed"), page.index("Undated"))
                self.assertIn("Publicado em: 24/10/2026", page)
                self.assertIn("Publicado em: 10/10/2026", page)
                self.assertIn("Publicado em: Data não informada", page)
                self.assertIn('id="monica-total-cards">3</strong>', page)
        finally:
            os.chdir(old_cwd)

if __name__=="__main__":unittest.main()
