import unittest
from pathlib import Path

class RegionalCompanyLabelsTests(unittest.TestCase):
 def test_collected_vs_monitored_copy(self):
  source=Path("src/unified_jobs_dashboard.py").read_text(encoding="utf-8")
  self.assertIn("Empresas com vagas coletadas:",source)
  self.assertIn("O filtro Empresa mostra somente empresas com vagas encontradas",source)
  self.assertIn("Empresas acompanhadas (",source)
  self.assertIn("A ausência de registros não significa ausência de contratações.",source)
