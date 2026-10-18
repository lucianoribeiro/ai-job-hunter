import unittest
from src.recruiter_monitor import extract_application_contract, enrich_application

class ApplicationContractTests(unittest.TestCase):
    def test_vagas_com_clt(self):
        html='<html><body><h1>Supervisor de Produção</h1><p>Hyundai Mobis Brasil</p><span>Regime CLT</span></body></html>'
        info=extract_application_contract(html,'https://www.vagas.com.br/vagas/v2839698/supervisor-de-producao')
        self.assertEqual(info['contract_type'],'CLT')
        self.assertEqual(info['contract_source'],'Anúncio de candidatura')
    def test_unknown_or_unapproved_source(self):
        self.assertEqual(extract_application_contract('<p>Regime CLT</p>','https://other.example/vaga'),{})
        self.assertEqual(extract_application_contract('<p>Salário a combinar</p>','https://www.vagas.com.br/vagas/123'),{})
    def test_without_short_link_no_network_required(self):
        item={'title':'Supervisor de produção','contract_type':'Não informado'}
        self.assertEqual(enrich_application(item),item)
