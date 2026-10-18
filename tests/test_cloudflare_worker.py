"""Contract checks for the public AI Worker used by the static dashboard."""
import unittest
from pathlib import Path


class CloudflareWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("cloudflare/match-worker/index.js").read_text(encoding="utf-8")

    def test_cv_route_is_implemented_for_dashboard_contract(self):
        self.assertIn('@cf/meta/llama-3.3-70b-instruct-fp8-fast', self.source)
        self.assertIn('["/match","/cv"]', self.source)
        self.assertIn('if(pathname==="/cv")', self.source)
        self.assertIn('return json({cv,method:', self.source)
        dashboard = Path("src/unified_jobs_dashboard.py").read_text(encoding="utf-8")
        self.assertIn("fetch(endpoint+'/cv'", dashboard)

    def test_cv_prompt_is_professional_and_forbids_fabrication(self):
        required = (
            "compatíveis com ATS", "Não invente empresas", "ordem cronológica inversa",
            "Resumo profissional", "características protegidas", "Retorne apenas o currículo final",
            'Nunca escreva "não informado"', "Uma competência mencionada não prova uma realização",
            "Write 100% in professional international English",
        )
        for phrase in required:
            self.assertIn(phrase, self.source)

    def test_cv_requires_consent_and_bounded_input(self):
        self.assertIn('payload?.consent!==true', self.source)
        self.assertIn('profile.length>30000', self.source)
        self.assertIn('["pt","en"].includes(language)', self.source)


if __name__ == "__main__":
    unittest.main()
