import json
import tempfile
import unittest
from pathlib import Path
from src.monica_regional_discovery import regional_scope, discover, reconcile

class RegionalDiscoveryTests(unittest.TestCase):
    def job(self,title="Coordenador de Projetos",location="Nova Odessa, SP"):
        return {"title":title,"location":location,"url":"https://jobs.lever.co/test/1"}
    def test_nova_odessa_first(self):
        self.assertEqual(regional_scope(self.job()),1)
        self.assertEqual(regional_scope(self.job(location="Campinas, SP")),2)
    def test_excludes_other_state_and_unrelated_role(self):
        self.assertIsNone(regional_scope(self.job(location="Curitiba, PR")))
        self.assertIsNone(regional_scope(self.job(title="Coordenador de Produção")))
        self.assertIsNone(regional_scope(self.job(location="Não informado")))
    def test_remote_brazil(self):
        self.assertEqual(regional_scope(self.job(location="Remote, Brazil")),3)
    def test_merge_dedupe_preserves_valid_jobs(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a.json";b=Path(d)/"b.json"
            a.write_text(json.dumps({"jobs":[self.job(location="Campinas, SP")]}))
            b.write_text(json.dumps({"jobs":[self.job(location="Nova Odessa, SP")]}))
            jobs,stats=discover([a,b])
            self.assertEqual(len(jobs),1)
            self.assertEqual(jobs[0]["regional_priority"],1)
            self.assertEqual(len(stats),2)
    def test_first_seen_survives_and_missing_job_is_preserved(self):
        old = [{**self.job(), "first_seen_at": "2026-10-20T10:00:00+00:00",
                "last_seen_at": "2026-10-21T10:00:00+00:00"}]
        current = reconcile([self.job()], old, "2026-10-25T10:00:00+00:00")
        self.assertEqual(current[0]["first_seen_at"], "2026-10-20T10:00:00+00:00")
        self.assertEqual(current[0]["last_seen_at"], "2026-10-25T10:00:00+00:00")
        self.assertFalse(current[0]["not_seen_in_latest_collection"])
        missing = reconcile([], current, "2026-10-26T10:00:00+00:00")
        self.assertEqual(len(missing), 1)
        self.assertTrue(missing[0]["not_seen_in_latest_collection"])

    def test_failed_source_is_isolated(self):
        jobs,stats=discover([Path("/file/that/does/not/exist")])
        self.assertEqual(jobs,[])
        self.assertEqual(list(stats.values())[0]["status"],"failed")
if __name__=="__main__":unittest.main()
