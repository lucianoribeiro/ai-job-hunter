import unittest
from src.unified_jobs_dashboard import render, recruiter_index_date

class RecruiterSummaryTests(unittest.TestCase):
 def test_brazil_time(self):
  self.assertEqual(recruiter_index_date("2026-10-18T14:45:27+00:00")[0],"18/10/2026 às 11h45")
 def test_collection_and_filtered_totals_separated(self):
  page=render({"jobs":[]},[])
  for expected in ('Última coleta','Horário de Brasília','Publicações coletadas','Resultados exibidos','id="recruiter-total"','id="recruiter-count"','aria-live="polite"'):
   self.assertIn(expected,page)
  self.assertNotIn('Data UTC:',page)
  self.assertIn("count.textContent=String(visible)",page)
  self.assertIn('Coleta concluída sem erros reportados',page)
