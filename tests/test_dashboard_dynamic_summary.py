"""Regression coverage for dynamic, filter-aware dashboard summary cards."""
import unittest

from src.unified_jobs_dashboard import render


class DynamicSummaryTests(unittest.TestCase):
    def test_summary_cards_follow_same_filtered_rows(self):
        page = render({"jobs": []}, [])
        for element in ('summary-total', 'summary-qa', 'summary-projects'):
            self.assertIn('id="' + element + '"', page)
        self.assertIn('let visible=0,qaVisible=0,projectsVisible=0', page)
        self.assertIn("if(r.dataset.area==='QA')qaVisible++", page)
        self.assertIn("else if(r.dataset.area==='Projetos')projectsVisible++", page)
        self.assertIn("document.getElementById('summary-total').textContent=String(visible)", page)
        self.assertIn("document.getElementById('summary-qa').textContent=String(qaVisible)", page)
        self.assertIn("document.getElementById('summary-projects').textContent=String(projectsVisible)", page)
        self.assertIn("[q,a,m,source,region,city,age,usdFilter].forEach(el=>el.addEventListener('input',apply))", page)


if __name__ == "__main__":
    unittest.main()
