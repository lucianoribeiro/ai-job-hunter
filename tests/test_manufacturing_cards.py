import unittest
from src.unified_jobs_dashboard import render

class ManufacturingCardsTests(unittest.TestCase):
    def test_manufacturing_cards_are_readable_and_qa_unchanged(self):
        page=render({'jobs': []}, [])
        self.assertIn('Região prioritária', page)
        self.assertIn('Ver publicação original', page)
        self.assertIn('Prazo informado vencido', page)
        self.assertIn('seen_manufacturing', open('src/unified_jobs_dashboard.py', encoding='utf-8').read())
        self.assertIn('id="recruiter-area"', page)
