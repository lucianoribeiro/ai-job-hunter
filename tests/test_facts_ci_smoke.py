import unittest
from src.recruiter_monitor import extract_job_facts
class FactsSmoke(unittest.TestCase):
 def test_no_guess(self):
  self.assertEqual(extract_job_facts('Gerente de produção Campinas')['modality'],'Não informada')
