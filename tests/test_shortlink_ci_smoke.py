import unittest
from src.recruiter_monitor import extract_application_contract
class ShortlinkSmoke(unittest.TestCase):
 def test_explicit(self):
  self.assertEqual(extract_application_contract('<span>Regime CLT</span>','https://www.vagas.com.br/vagas/example')['contract_type'],'CLT')
