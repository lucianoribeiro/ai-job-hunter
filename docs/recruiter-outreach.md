# Recruiter email discovery and Gmail draft review

This integration is **opt-in** and does not scrape LinkedIn, access a user's mailbox, or auto-send emails.

## Workflow

1. Copy a LinkedIn recruitment post that explicitly invites QA applicants to email a CV into a **private local** UTF-8 file.
2. Create a **private local** profile JSON with your real name and reviewed strengths, e.g.
   `{"name":"Your Name","strengths":["QA automation","QA team leadership"]}`.
3. Keep your PDF CV outside the repository.
4. Run:

```bash
python -m unittest discover -s tests -v
python -m src.recruiter_outreach --post /private/post.txt --profile /private/profile.json --cv /private/CV.pdf
```

5. Review the resulting private `.local/outreach/draft.json`. Verify authenticity of the recruiter, employer, and whether the post asks for email applications.
6. To create an **actual Gmail draft**, explicitly provide the verified post, recipient, approved email text and CV in your ChatGPT conversation, and request draft creation via the connected Gmail app. This is a separate user-authorized step; it does not send the email.
7. In Gmail, inspect recipient, text, and CV attachment; send only after you explicitly approve.

## Safety / implementation boundaries

- The extractor recognizes explicitly stated professional emails near application language, but it **cannot verify identity or company legitimacy**.
- No recipient enrichment, email guessing, bulk sends, automatic scraping or hidden posting.
- The draft generator does not connect to Gmail or attach files. It prepares reviewable content only.
- The default draft makes no unsupported claims about salary, skills, years of experience, or recruiter identity.
- Keep posts, recipient email addresses, resumes and private notes out of public Git repositories and CI artifacts.
