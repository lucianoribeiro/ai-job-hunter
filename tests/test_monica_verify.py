import unittest
from src.monica_verify import verify,allowed
class VerificationTests(unittest.TestCase):
    def test_no_social_scraping(self):
        self.assertFalse(allowed("https://www.linkedin.com/jobs/view/1"))
        self.assertFalse(allowed("http://jobs.lever.co/test/1"))
        self.assertFalse(allowed("https://jobs.lever.co.evil.test/job"))
    def test_closed(self):
        res=verify({"url":"https://jobs.lever.co/foo/123"},
                   getter=lambda _: "<html><body>Não aceita mais candidaturas</body></html>")
        self.assertEqual(res["status"],"closed")
    def test_open_indication(self):
        res=verify({"url":"https://job-boards.greenhouse.io/foo/jobs/123"},
                   getter=lambda _: "<main><button>Apply for this job</button></main>")
        self.assertEqual(res["status"],"apply_indicated")
    def test_script_text_not_decisive(self):
        res=verify({"url":"https://jobs.lever.co/foo/123"},
                   getter=lambda _: "<script>job expired</script><main>Details</main>")
        self.assertEqual(res["status"],"unverified")
    def test_failure_unverified(self):
        def fail(_): raise OSError()
        self.assertEqual(verify({"url":"https://jobs.lever.co/foo/1"},fail)["status"],"unverified")
if __name__=="__main__": unittest.main()
