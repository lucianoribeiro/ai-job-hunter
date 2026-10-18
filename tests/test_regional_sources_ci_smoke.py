import unittest
from src.strategic_companies import inspect_petrobras_concursos
class RegionalSmoke(unittest.TestCase):
 def test_closed(self):
  self.assertTrue(inspect_petrobras_concursos('Não temos inscrições abertas para concursos no momento'))
