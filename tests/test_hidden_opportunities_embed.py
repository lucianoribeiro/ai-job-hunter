import json
import os
import tempfile
import unittest
from pathlib import Path
from src.hidden_market_embed import embed


class HiddenOpportunityEmbedTests(unittest.TestCase):
    def test_agent_reach_section_is_published_as_potential(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = os.getcwd()
            try:
                os.chdir(tmp)
                Path("data").mkdir()
                Path("site").mkdir()
                Path("site/index.html").write_text(
                    '<div id="mainPanelGeneral" class="primary-panel" role="tabpanel" aria-labelledby="mainTabGeneral"></div>',
                    encoding="utf-8"
                )
                Path("data/hidden_market.json").write_text(json.dumps({
                    "items": [], "companies_checked": 0, "companies_failed": 0
                }), encoding="utf-8")
                Path("data/hidden_opportunities.json").write_text(json.dumps({
                    "items": [{"url": "https://www.linkedin.com/posts/company_hiring-qa",
                               "excerpt": "Explorando liderança em QA"}],
                    "records_examined": 1, "signals": 1, "collector_status": "complete"
                }), encoding="utf-8")
                embed(Path("site/index.html"), Path("data/hidden_market.json"))
                page = Path("site/index.html").read_text(encoding="utf-8")
                self.assertIn('id="hidden-opportunities-agent-reach"', page)
                self.assertIn("Hidden Opportunity · Potencial", page)
                self.assertIn("não vagas confirmadas", page)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
