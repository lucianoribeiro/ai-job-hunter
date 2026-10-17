"""Regression tests for the APinfo external-source panel."""
import unittest
from src.dashboard import render


class APinfoSourceTests(unittest.TestCase):
    def test_apinfo_link_and_manual_status(self):
        output = render({})
        self.assertIn('https://www.apinfo.com/apinfo/', output)
        self.assertIn('integração automática não habilitada', output)
        self.assertIn('Não há API pública oficial confirmada', output)

    def test_apinfo_does_not_add_fake_jobs(self):
        output = render({})
        self.assertIn('Vagas registradas</span><strong>0</strong>', output)
        self.assertIn('<tbody></tbody>', output)


if __name__ == "__main__":
    unittest.main()
