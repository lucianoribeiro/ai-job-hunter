import json
import tempfile
import unittest
from pathlib import Path
from src.monica_digest import update

JOB={"url":"https://jobs.lever.co/org/one","title":"Project Manager","company":"Example",
"location":"Campinas, SP","location_class":"regional","score":88,
"application_status":"apply_indicated","matches":["NPI"]}
def other(url):return dict(JOB,url=url)

class DigestTests(unittest.TestCase):
    def test_initial_baseline_then_accumulate_and_digest_only_once(self):
        with tempfile.TemporaryDirectory() as d:
            feed=Path(d)/"feed.json"
            state=Path(d)/"state.json"
            sent=[]
            def write(jobs):feed.write_text(json.dumps({"jobs":jobs}),encoding="utf-8")
            write([JOB])
            self.assertTrue(update(feed,state,False,True,lambda jobs:sent.append(jobs))["initial"])
            write([JOB,other("https://jobs.lever.co/org/two")])
            self.assertEqual(update(feed,state,False,True,lambda jobs:sent.append(jobs))["queued"],1)
            self.assertEqual(len(sent),0)
            self.assertEqual(update(feed,state,True,True,lambda jobs:sent.append(jobs))["sent"],1)
            self.assertEqual(update(feed,state,True,True,lambda jobs:sent.append(jobs))["sent"],0)
            self.assertEqual(len(sent),1)
    def test_disabled_email_preserves_pending(self):
        with tempfile.TemporaryDirectory() as d:
            feed=Path(d)/"feed.json";state=Path(d)/"state.json";sent=[]
            feed.write_text(json.dumps({"jobs":[JOB]}));update(feed,state)
            feed.write_text(json.dumps({"jobs":[JOB,other("https://jobs.lever.co/org/2")]}))
            self.assertEqual(update(feed,state,True,False,lambda jobs:sent.append(jobs))["queued"],1)
            self.assertEqual(update(feed,state,True,True,lambda jobs:sent.append(jobs))["sent"],1)
    def test_excludes_unverified_closed_and_low_score(self):
        with tempfile.TemporaryDirectory() as d:
            feed=Path(d)/"feed.json";state=Path(d)/"state.json"
            feed.write_text(json.dumps({"jobs":[]}));update(feed,state)
            jobs=[dict(JOB,url="https://jobs.lever.co/org/u",application_status="unverified"),
                  dict(JOB,url="https://jobs.lever.co/org/c",application_status="closed"),
                  dict(JOB,url="https://jobs.lever.co/org/l",score=50)]
            feed.write_text(json.dumps({"jobs":jobs}))
            self.assertEqual(update(feed,state)["queued"],0)
    def test_failed_delivery_preserves_pending(self):
        with tempfile.TemporaryDirectory() as d:
            feed=Path(d)/"feed.json";state=Path(d)/"state.json"
            feed.write_text(json.dumps({"jobs":[]}));update(feed,state)
            feed.write_text(json.dumps({"jobs":[JOB]}))
            def failing(jobs):raise RuntimeError("SMTP failure")
            with self.assertRaises(RuntimeError):
                update(feed,state,True,True,failing)
            self.assertEqual(update(feed,state)["queued"],1)
if __name__=="__main__":unittest.main()
