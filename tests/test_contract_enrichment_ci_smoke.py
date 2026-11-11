import unittest
from src.recruiter_monitor import extract_application_contract
class ContractSmoke(unittest.TestCase):
 def test_clt(self):
  facts=extract_application_contract('<p>Regime CLT</p>','https://www.vagas.com.br/vagas/test')
  self.assertEqual(facts['contract_type'],'CLT')
