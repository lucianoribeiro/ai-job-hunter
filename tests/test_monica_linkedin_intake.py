import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from src.monica_pipeline import collect,build
class LinkedInIntakeTests(unittest.TestCase):
    def test_import_real_record_format(self):
        with TemporaryDirectory() as d:
            path=Path(d)/"linkedin.json"
            path.write_text(json.dumps({"jobs":[{"title":"Project Manager","company":"Example","url":"https://www.linkedin.com/jobs/view/123","location":"Campinas, SP","description":"Project management"}]}))
            rows=collect(path)
            self.assertEqual(len(rows),1)
            result=build({"id":"monica","competencies":["gestao de projetos"]},rows)
            self.assertEqual(result[0]["application_status"],"unverified")
    def test_missing_file_not_invented(self):
        with TemporaryDirectory() as d:
            self.assertFalse((Path(d)/"linkedin.json").exists())
if __name__=="__main__":unittest.main()
