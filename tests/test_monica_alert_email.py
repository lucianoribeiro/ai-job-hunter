import unittest
import tempfile
import json
from pathlib import Path
from src.monica_alert_email import run, qualified, render_email
J={"url":"https://jobs.lever.co/a/1","title":"NPI Project Manager","company":"Example","location":"Campinas","location_class":"regional","application_status":"apply_indicated","score":90,"matches":["npi"]}
class AlertEmailTests(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(qualified({**J,"application_status":"unverified"}))
        self.assertFalse(qualified({**J,"location_class":"remote_review"}))
        self.assertFalse(qualified({**J,"score":45}))
    def test_first_run_baseline_and_dedup(self):
        with tempfile.TemporaryDirectory() as d:
            feed=Path(d)/"jobs.json";state=Path(d)/"state.json";sent=[]
            feed.write_text(json.dumps({"jobs":[J]}))
            self.assertTrue(run(feed,state,True,lambda j:sent.append(j))["initial"])
            self.assertEqual(sent,[])
            self.assertEqual(run(feed,state,True,lambda j:sent.append(j))["new"],0)
            feed.write_text(json.dumps({"jobs":[J,{**J,"url":"https://jobs.lever.co/a/2"}]}))
            self.assertEqual(run(feed,state,True,lambda j:sent.append(j))["new"],1)
            self.assertEqual(len(sent),1)
    def test_email_template(self):
        self.assertIn("NPI Project Manager",render_email([J]))
if __name__=="__main__":unittest.main()
