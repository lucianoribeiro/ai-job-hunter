import unittest
from src.unified_jobs_dashboard import render

class DistinctStudioPanelsTests(unittest.TestCase):
    def test_each_tab_has_own_form_and_output(self):
        page=render({"jobs":[]},[])
        for panel in ("studioFitPanel","studioCvPanel","studioApplicationPanel","studioCareerPanel"):
            self.assertIn('id="'+panel+'"',page)
        self.assertIn('id="studioCvText"',page)
        self.assertIn('id="studioAppRole"',page)
        self.assertIn('id="studioCareerGoal"',page)
        self.assertIn("panel.hidden=key!==btn.dataset.task",page)
        self.assertIn("studioCvPrepare",page)
        self.assertIn("studioAppPrepare",page)
        self.assertIn("studioCareerPrepare",page)
        self.assertIn("textContent=value",page)

    def test_fit_is_the_only_panel_showing_job_selector(self):
        page=render({"jobs":[]},[])
        fit=page.split('id="studioFitPanel"',1)[1].split('id="studioCvPanel"',1)[0]
        self.assertIn('id="aiJob"',fit)
        cv=page.split('id="studioCvPanel"',1)[1].split('id="studioApplicationPanel"',1)[0]
        self.assertNotIn('id="aiJob"',cv)
