import unittest
from src.recruiter_monitor import advertised_usd_salary
class QaUsdSmoke(unittest.TestCase):
    def test_hourly(self):
        self.assertEqual(advertised_usd_salary('US$ 63 a US$ 120 por hora'), 'US$ 63–120 /hora')
