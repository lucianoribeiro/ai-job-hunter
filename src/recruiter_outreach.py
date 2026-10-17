"""Privacy-first recruiter post intake and application draft generation.

Processes user-provided post text only; never scrapes LinkedIn or sends email.
Recipient and all drafts are stored only in a local, git-ignored folder.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

LOCAL = Path(".local/outreach")
ADDRESS = re.compile(r"(?<![\w.+-])([A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9][A-Za-z0-9.\-]*\.[A-Za-z]{2,})(?![\w.-])")
CALL_TO_APPLY = re.compile(r"\b(send|email|submit|apply|forward|share)\b.{0,100}\b(cv|resume|résumé|application|profile)\b|\b(cv|resume|résumé)\b.{0,100}\b(to|at)\b", re.I | re.S)
QA = re.compile(r"\b(QA|quality assurance|quality engineer|quality engineering|software test(?:er|ing)?|SDET|test automation|QA lead|QA manager)\b", re.I)


def candidates(post: str) -> list[dict]:
    """A post must explicitly invite applications; email alone is not permission."""
    if not QA.search(post) or not CALL_TO_APPLY.search(post):
        return []
    found = []
    for match in ADDRESS.finditer(post):
        email = match.group(1).lower()
        snippet = post[max(0, match.start() - 130):match.end() + 130]
        if not re.search(r"\b(apply|applications?|send|resume|résumé|cv|email|recruit(?:er|ment)|hiring)\b", snippet, re.I):
            continue
        if email not in {x["email"] for x in found}:
            found.append({"email": email, "evidence": "email explicitly shown near recruitment/application text",
                          "needs_human_verification": True})
    return found


def create_draft(post: str, recipient: str, profile: dict, cv_filename: str) -> dict:
    approved = {item["email"] for item in candidates(post)}
    if recipient.lower() not in approved:
        raise ValueError("Recipient not found in an explicit QA application request")
    if not cv_filename.lower().endswith(".pdf"):
        raise ValueError("Provide the name of a PDF CV to attach manually in Gmail")
    full_name = str(profile.get("name", "")).strip()
    strengths = [str(x).strip() for x in profile.get("strengths", []) if str(x).strip()]
    if not full_name or not strengths:
        raise ValueError("A name and reviewed strengths must be provided privately")
    # Do not fabricate job title, recruiter name, salary, achievements or years.
    subject = "Application — QA / Quality Engineering opportunity"
    body = (
        "Hello,\n\n"
        "I saw your post inviting applications for a QA / Quality Engineering opportunity "
        "and would like to express my interest.\n\n"
        "My relevant experience includes " + ", ".join(strengths[:4]) + ". "
        "I would welcome the opportunity to learn more about the role, its remote-work "
        "requirements, and the expected workload.\n\n"
        "Please find my CV attached for your consideration.\n\n"
        "Best regards,\n" + full_name
    )
    return {"to": recipient.lower(), "subject": subject, "body": body,
            "attachment_to_add": cv_filename, "status": "requires_review",
            "send_allowed": False, "source": "user_supplied_linkedin_post",
            "checklist": ["Confirm genuine recruiter and company", "Confirm contact requests applications",
                          "Verify remote eligibility, work hours and pay", "Review email and attach CV"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a review-only recruiter email draft")
    parser.add_argument("--post", type=Path, required=True, help="Private text file containing LinkedIn post")
    parser.add_argument("--profile", type=Path, required=True, help="Private JSON file with name and reviewed strengths")
    parser.add_argument("--cv", type=Path, required=True, help="Private PDF CV path")
    parser.add_argument("--recipient", help="Recipient to use if the post provides several addresses")
    args = parser.parse_args()
    if not args.cv.is_file() or args.cv.suffix.lower() != ".pdf":
        parser.error("CV must be an existing PDF file")
    post = args.post.read_text(encoding="utf-8")
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    contacts = candidates(post)
    if not contacts:
        parser.error("No explicit QA application email was found in the supplied post")
    if not args.recipient and len(contacts) > 1:
        parser.error("Multiple emails found; choose one using --recipient")
    recipient = args.recipient or contacts[0]["email"]
    output = create_draft(post, recipient, profile, args.cv.name)
    LOCAL.mkdir(parents=True, exist_ok=True)
    dest = LOCAL / "draft.json"
    if dest.exists():
        parser.error("Private draft already exists; review or move it before generating another")
    dest.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Review-only draft saved to {dest}; NOT sent or uploaded to Gmail.")


if __name__ == "__main__":
    main()
