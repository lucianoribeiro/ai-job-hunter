"""Regression checks for recruiter email handoff and authenticated Gmail drafts."""
import unittest
from pathlib import Path

from src.unified_jobs_dashboard import recruiter_email


class RecruiterOutreachGmailTests(unittest.TestCase):
    def test_extracts_only_explicit_valid_email(self):
        self.assertEqual(recruiter_email("Envie CV para Jobs.QA+lead@Example.com"), "jobs.qa+lead@example.com")
        self.assertEqual(recruiter_email("Fale comigo pelo LinkedIn"), "")
        self.assertEqual(recruiter_email("texto @ sem dominio"), "")

    def test_monitor_card_signals_email_and_uses_configured_authenticated_app(self):
        # The rendered monitor reads its public feed from data; verify the handoff implementation itself remains scoped.
        source = Path("src/unified_jobs_dashboard.py").read_text(encoding="utf-8")
        self.assertIn('class="recruiter-card-actions"', source)
        self.assertIn('class="recruiter-cta recruiter-cta-secondary"', source)
        self.assertIn('class="recruiter-cta recruiter-cta-primary"', source)
        self.assertIn("CAREER_APP_URL", source)
        self.assertIn('os.environ.get("CAREER_APP_URL") or "https://ai-job-hunter-lucianoribeiro.vercel.app"', source)
        self.assertIn("Preparar candidatura com CV", source)
        self.assertIn('"recipient": contact', source)

    def test_gmail_flow_has_explicit_send_and_draft_with_pdf_attachment(self):
        gmail = Path("app/lib/gmail-api.ts").read_text(encoding="utf-8")
        action = Path("app/app/applications/outreach/[id]/compose/actions.ts").read_text(encoding="utf-8")
        oauth = Path("app/app/actions.ts").read_text(encoding="utf-8")
        self.assertIn("/gmail/v1/users/me/drafts", gmail)
        self.assertIn("/messages/send", gmail)
        self.assertIn("sendApprovedRecruiterEmail", action)
        self.assertIn("gmail.send", oauth)
        self.assertIn('status:"sent"', action)
        self.assertIn('status:"sending"', action)
        self.assertIn("application/pdf", gmail)
        self.assertIn("gmail.compose", oauth)
        self.assertIn("professionalResumePdf", action)
        self.assertIn('status:"drafted"', action)

    def test_composite_foreign_keys_have_unique_parent_indexes(self):
        foundation = Path("db/001_saas_foundation.sql").read_text(encoding="utf-8")
        resumes = Path("db/002_resume_studio.sql").read_text(encoding="utf-8")
        self.assertIn("opportunities_id_user_id_uidx", foundation)
        self.assertIn("on public.opportunities(id, user_id)", foundation)
        self.assertIn("resume_versions_id_user_id_uidx", resumes)
        self.assertIn("on public.resume_versions(id,user_id)", resumes)


if __name__ == "__main__":
    unittest.main()
