import unittest
from src.hunter import greenhouse_role, greenhouse_project_location, classify

CONFIG = {"blocked_title_terms": ["sales", "recruiter", "marketing", "account executive"],
 "full_time_keywords": ["qa engineer", "qa manager", "qa tech lead", "project manager",
 "project coordinator", "analista de projetos"], "freelance_keywords": ["qa"],
 "remote_required": True}

def make_job(title, location="Campinas, São Paulo, Brazil", source="Greenhouse", remote=False):
    return {"id": "greenhouse:test:1", "title": title, "company": "Example",
        "source": source, "location": location, "type": "", "salary": "",
        "description": "", "url": "https://example.com/1", "remote": remote}

class GreenhouseRoleTests(unittest.TestCase):
    def test_supported_roles(self):
        samples = {
            "QA Engineer": "QA", "QA Manager": "QA",
            "QA Tech Lead": "QA", "Tech Lead QA": "QA",
            "Technical Lead QA": "QA",
            "Analista de Projetos": "Analista de Projetos",
            "Project Analyst": "Analista de Projetos",
            "Gerente de Projetos": "Gerente de Projetos",
            "Project Manager": "Gerente de Projetos",
            "Coordenador de Projetos": "Coordenador de Projetos",
            "Project Coordinator": "Coordenador de Projetos"}
        for title, expected in samples.items():
            with self.subTest(title=title):
                self.assertEqual(greenhouse_role(title), expected)

    def test_region_project_not_remote(self):
        found = classify(make_job("Analista de Projetos"), CONFIG)
        self.assertIsNotNone(found)
        self.assertEqual(found["role"], "Analista de Projetos")
        self.assertFalse(found["remote"])

    def test_qa_not_expanded_to_local_non_remote(self):
        self.assertIsNone(classify(make_job("QA Manager"), CONFIG))

    def test_qa_remote_included(self):
        found = classify(make_job("QA Tech Lead", location="Remote", remote=True), CONFIG)
        self.assertIsNotNone(found)
        self.assertEqual(found["role"], "QA")

    def test_outside_region_non_remote_excluded(self):
        self.assertIsNone(classify(make_job("Project Manager", "Lisbon, Portugal"), CONFIG))

    def test_other_sources_unchanged(self):
        self.assertIsNone(classify(make_job("Project Manager", source="Remotive"), CONFIG))

    def test_no_false_positive_title(self):
        for title in ("Production Coordinator", "Sales Manager", "Product Manager", "Tech Lead"):
            self.assertIsNone(greenhouse_role(title))

if __name__ == "__main__":
    unittest.main()
