import unittest
from src.recruiter_monitor import classify

class SmokeTest(unittest.TestCase):
    def test_factory_leadership(self):
        self.assertEqual(classify('Plant Manager hiring')['area'], 'Manufatura')
