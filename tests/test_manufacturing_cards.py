import unittest
from src.unified_jobs_dashboard import render

class ManufacturingCardsTests(unittest.TestCase):
    def test_manufacturing_cards_are_readable_and_qa_unchanged(self):
        page=render({'jobs': []}, [])
        source=open('src/unified_jobs_dashboard.py', encoding='utf-8').read()
        self.assertIn('Região prioritária', source)
        self.assertIn('Ver publicação original', source)
        self.assertIn('Prazo informado vencido', source)
        self.assertIn('seen_manufacturing', source)
        self.assertIn('id="recruiter-area"', page)
