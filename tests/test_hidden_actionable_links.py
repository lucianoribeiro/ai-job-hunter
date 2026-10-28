import json
import os
import tempfile
import unittest
from pathlib import Path
from src.hidden_market_embed import embed


class ActionableHiddenLinkTests(unittest.TestCase):
    def test_public_post_link_and_status_are_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            previous = os.getcwd()
            try:
                os.chdir(temp)
                Path("data").mkdir()
                Path("site").mkdir()
                Path("site/index.html").write_text(
                    '<div id="mainPanelGeneral" class="primary-panel" role="tabpanel" aria-labelledby="mainTabGeneral"></div>', encoding="utf-8")
                Path("data/hidden_market.json").write_text(
                    json.dumps({"items": [], "companies_checked": 2}), encoding="utf-8")
                link = "https://example.org/qa-role"
                Path("data/hidden_opportunities.json").write_text(json.dumps({
                    "records_examined": 1, "signals": 1, "collector_status": "complete",
                    "items": [{"url": link, "excerpt": "Contract QA Lead: Build Automation & Strategy (Hybrid) in Belfast. At a Glance - Tasks: Lead testing."}]
                }), encoding="utf-8")
                embed(Path("site/index.html"), Path("data/hidden_market.json"))
                page = Path("site/index.html").read_text(encoding="utf-8")
                self.assertIn('Abrir publicação original', page)
                self.assertIn(link, page)
                self.assertIn("Vaga pública identificada", page)
                self.assertIn("não uma oportunidade oculta", page)
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
