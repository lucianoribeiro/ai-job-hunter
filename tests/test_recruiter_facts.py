import unittest
from src.recruiter_monitor import extract_job_facts
from src.unified_jobs_dashboard import render

class RecruiterFactsTests(unittest.TestCase):
 def test_explicit_remote_usd_and_b2b(self):
  facts=extract_job_facts("QA Engineer 100% remoto B2B USD 6500 per month")
  self.assertEqual(facts["modality"],"Remoto confirmado")
  self.assertEqual(facts["contract_type"],"B2B")
  self.assertEqual(facts["salary_usd"],"US$ 6500 /mês")
  self.assertTrue(facts["salary_evidence"])
 def test_location_is_not_onsite(self):
  facts=extract_job_facts("Vaga Gerente de Produção Hortolândia SP Grupo EMS")
  self.assertEqual(facts["modality"],"Não informada")
  self.assertIsNone(facts["salary_usd"])
 def test_ambiguous_dollar_and_conflicting_modes_not_confirmed(self):
  facts=extract_job_facts("QA remoto e presencial, $5000")
  self.assertEqual(facts["modality"],"Não informada")
  self.assertIsNone(facts["salary_usd"])
 def test_explicit_hybrid_and_clt(self):
  facts=extract_job_facts("QA híbrido CLT")
  self.assertEqual(facts["modality"],"Híbrido confirmado")
  self.assertEqual(facts["contract_type"],"CLT")
 def test_dashboard_has_contract_filter(self):
  page=render({"jobs":[]}, [])
  self.assertIn('id="recruiter-contract"',page)
  self.assertIn('card.dataset.contract===recruiterContract.value',page)
  self.assertIn('data-contract=',page)
