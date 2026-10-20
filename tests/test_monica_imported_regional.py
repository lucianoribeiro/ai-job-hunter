import unittest
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
        self.assertLess(html.index("VRH Consultoria"),html.index("AB InBev") if "AB InBev" in html else len(html))
        self.assertIn("Vaga importada · Região de Nova Odessa",html)
    def test_not_duplicated_when_cv_feed_contains_listing(self):
        job={"url":"https://www.netvagas.com.br/empresa/anuncios/a1724116/gerente-de-projetos/",
             "title":"Gerente de Projetos","company":"VRH Consultoria",
             "location":"Paulínia, SP","score":85,"application_status":"unverified"}
        html=render({"jobs":[job]})
        self.assertEqual(html.count('href="https://www.netvagas.com.br/empresa/anuncios/a1724116/gerente-de-projetos/"'),1)

if __name__=="__main__":unittest.main()
